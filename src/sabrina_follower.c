#include "global.h"
#include "event_data.h"
#include "event_object_movement.h"
#include "field_player_avatar.h"
#include "fieldmap.h"
#include "link.h"
#include "metatile_behavior.h"
#include "overworld.h"
#include "quest_log.h"
#include "sabrina_follower.h"
#include "script.h"
#include "constants/event_object_movement.h"
#include "constants/event_objects.h"
#include "constants/flags.h"
#include "constants/maps.h"
#include "constants/region_map_sections.h"
#include "constants/trainer_types.h"

#define TRAIL_LENGTH 8

extern const u8 Sabrina_EventScript_Companion[];
extern const u8 Sabrina_EventScript_PalletTown[];
extern const u8 Sabrina_EventScript_ViridianCity[];
extern const u8 Sabrina_EventScript_PewterCity[];
extern const u8 Sabrina_EventScript_CeruleanCity[];
extern const u8 Sabrina_EventScript_VermilionCity[];
extern const u8 Sabrina_EventScript_LavenderTown[];
extern const u8 Sabrina_EventScript_CeladonCity[];
extern const u8 Sabrina_EventScript_FuchsiaCity_PokemonCenter_1F[];
extern const u8 Sabrina_EventScript_SaffronCity[];
extern const u8 Sabrina_EventScript_CinnabarIsland[];
extern const u8 Sabrina_EventScript_IndigoPlateau_PokemonCenter_1F[];
extern const u8 Sabrina_EventScript_OneIsland[];

struct FollowerStep
{
    struct Coords16 pos;
    u8 fast;
};

static EWRAM_DATA struct
{
    struct FollowerStep steps[TRAIL_LENGTH];
    struct Coords16 playerPos;
    u8 mapNum;
    u8 mapGroup;
    u8 head;
    u8 count;
    bool8 ready;
    bool8 talking;
} sFollower = {0};

// Some engine helpers look up a map template even for special objects. This
// read-only template keeps those lookups valid without consuming a map slot.
static const struct ObjectEventTemplate sFollowerTemplate =
{
    .localId = LOCALID_SABRINA_FOLLOWER,
    .graphicsId = OBJ_EVENT_GFX_SABRINA,
    .kind = OBJ_KIND_NORMAL,
    .script = Sabrina_EventScript_Companion,
    .flagId = 0,
};

bool8 IsSabrinaFollower(const struct ObjectEvent *objectEvent)
{
    return objectEvent->active && objectEvent->localId == LOCALID_SABRINA_FOLLOWER;
}

const struct ObjectEventTemplate *GetSabrinaFollowerTemplate(void)
{
    return &sFollowerTemplate;
}

const u8 *GetSabrinaFollowerScript(void)
{
    sFollower.talking = TRUE;
    // Town interiors share the town's dialogue. Routes use companion dialogue.
    // Never return the Gym battle script from a traveling conversation.
    switch (gMapHeader.regionMapSectionId)
    {
    case MAPSEC_PALLET_TOWN: return Sabrina_EventScript_PalletTown;
    case MAPSEC_VIRIDIAN_CITY: return Sabrina_EventScript_ViridianCity;
    case MAPSEC_PEWTER_CITY: return Sabrina_EventScript_PewterCity;
    case MAPSEC_CERULEAN_CITY: return Sabrina_EventScript_CeruleanCity;
    case MAPSEC_VERMILION_CITY: return Sabrina_EventScript_VermilionCity;
    case MAPSEC_LAVENDER_TOWN: return Sabrina_EventScript_LavenderTown;
    case MAPSEC_CELADON_CITY: return Sabrina_EventScript_CeladonCity;
    case MAPSEC_FUCHSIA_CITY: return Sabrina_EventScript_FuchsiaCity_PokemonCenter_1F;
    case MAPSEC_SAFFRON_CITY: return Sabrina_EventScript_SaffronCity;
    case MAPSEC_CINNABAR_ISLAND: return Sabrina_EventScript_CinnabarIsland;
    case MAPSEC_INDIGO_PLATEAU: return Sabrina_EventScript_IndigoPlateau_PokemonCenter_1F;
    case MAPSEC_ONE_ISLAND: return Sabrina_EventScript_OneIsland;
    default: return Sabrina_EventScript_Companion;
    }
}

static void RemoveFollowerObjects(void)
{
    u8 i;
    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        struct ObjectEvent *objectEvent = &gObjectEvents[i];
        if (IsSabrinaFollower(objectEvent))
            RemoveObjectEventByLocalIdAndMap(objectEvent->localId, objectEvent->mapNum, objectEvent->mapGroup);
    }
    sFollower.ready = FALSE;
    sFollower.count = 0;
    sFollower.head = 0;
}

static void RemoveStationaryCopies(void)
{
    u8 i;
    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        struct ObjectEvent *objectEvent = &gObjectEvents[i];
        if (objectEvent->active && objectEvent->graphicsId == OBJ_EVENT_GFX_SABRINA
            && objectEvent->localId != LOCALID_SABRINA_FOLLOWER)
            RemoveObjectEventByLocalIdAndMap(objectEvent->localId, objectEvent->mapNum, objectEvent->mapGroup);
    }
}

static bool8 IsInitialStoryMap(void)
{
    return (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_PALLET_TOWN)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_PALLET_TOWN))
        || (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB)
            && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_PALLET_TOWN_PROFESSOR_OAKS_LAB));
}

static bool8 ShouldSuppressFollower(struct ObjectEvent *player)
{
    if (!FlagGet(FLAG_SABRINA_FOLLOWER_ACTIVE) || player->invisible
        || QL_IS_PLAYBACK_STATE || InUnionRoom() || IsUpdateLinkStateCBActive())
        return TRUE;
    if (gSaveBlock1Ptr->location.mapGroup == MAP_GROUP(MAP_SAFFRON_CITY_GYM)
        && gSaveBlock1Ptr->location.mapNum == MAP_NUM(MAP_SAFFRON_CITY_GYM))
        return TRUE; // Preserve the original leader/badge/TM event without a duplicate.
    if (gPlayerAvatar.flags & (PLAYER_AVATAR_FLAG_MACH_BIKE | PLAYER_AVATAR_FLAG_ACRO_BIKE
        | PLAYER_AVATAR_FLAG_SURFING | PLAYER_AVATAR_FLAG_UNDERWATER))
        return TRUE;
    // Let scripted NPCs have their space. Oak's initial sequences are explicitly
    // supported: Red's scripted steps feed the same trail as normal walking.
    if (ArePlayerFieldControlsLocked() && !sFollower.talking
        && !IsInitialStoryMap())
        return TRUE;
    return FALSE;
}

static bool8 IsLandTile(s16 x, s16 y, u8 elevation)
{
    u8 z = MapGridGetElevationAt(x, y);
    return !MapGridGetCollisionAt(x, y) && GetMapBorderIdAt(x, y) != CONNECTION_INVALID
        && !MetatileBehavior_IsSurfable(MapGridGetMetatileBehaviorAt(x, y))
        && (z == 0 || elevation == 0 || z == elevation);
}

static bool8 IsOccupied(s16 x, s16 y, const struct ObjectEvent *player)
{
    u8 i;
    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        const struct ObjectEvent *objectEvent = &gObjectEvents[i];
        if (objectEvent->active && objectEvent != player && !IsSabrinaFollower(objectEvent)
            && ((objectEvent->currentCoords.x == x && objectEvent->currentCoords.y == y)
                || (objectEvent->previousCoords.x == x && objectEvent->previousCoords.y == y)))
            return TRUE;
    }
    return FALSE;
}

static bool8 IsSafeSpawnTile(s16 x, s16 y, struct ObjectEvent *player)
{
    u8 i;
    u8 behavior = MapGridGetMetatileBehaviorAt(x, y);
    if (!IsLandTile(x, y, player->currentElevation) || IsOccupied(x, y, player)
        || MetatileBehavior_IsWarpDoor(behavior) || MetatileBehavior_IsNonAnimDoor(behavior)
        || MetatileBehavior_IsLadder(behavior) || MetatileBehavior_IsWarpPad(behavior))
        return FALSE;
    // Do not materialize in a doorway, on a warp, or a coordinate cutscene tile.
    if (gMapHeader.events != NULL)
    {
        for (i = 0; i < gMapHeader.events->warpCount; i++)
            if (gMapHeader.events->warps[i].x + MAP_OFFSET == x
                && gMapHeader.events->warps[i].y + MAP_OFFSET == y)
                return FALSE;
        for (i = 0; i < gMapHeader.events->coordEventCount; i++)
            if (gMapHeader.events->coordEvents[i].x + MAP_OFFSET == x
                && gMapHeader.events->coordEvents[i].y + MAP_OFFSET == y)
                return FALSE;
    }
    return TRUE;
}

static u8 FindFollower(void)
{
    u8 i;
    u8 found = OBJECT_EVENTS_COUNT;
    for (i = 0; i < OBJECT_EVENTS_COUNT; i++)
    {
        if (IsSabrinaFollower(&gObjectEvents[i]))
        {
            if (found == OBJECT_EVENTS_COUNT)
                found = i;
            else
            {
                RemoveFollowerObjects();
                return OBJECT_EVENTS_COUNT;
            }
        }
    }
    return found;
}

static u8 SpawnFollower(struct ObjectEvent *player)
{
    u8 direction;
    u8 i;
    int id;
    s16 x, y;
    // Prefer behind Red, then try the other clear adjacent tiles. Never evict
    // another object if a crowded map exhausts the engine's 16 runtime slots.
    for (i = 0; i < 4; i++)
    {
        direction = (GetOppositeDirection(player->facingDirection) - 1 + i) % 4 + 1;
        x = player->currentCoords.x;
        y = player->currentCoords.y;
        MoveCoords(direction, &x, &y);
        if (!IsSafeSpawnTile(x, y, player))
            continue;
        id = SpawnSpecialObjectEventParameterized(OBJ_EVENT_GFX_SABRINA, MOVEMENT_TYPE_NONE,
            LOCALID_SABRINA_FOLLOWER, x, y, player->currentElevation);
        if (id >= OBJECT_EVENTS_COUNT)
            return OBJECT_EVENTS_COUNT;
        ObjectEventTurn(&gObjectEvents[id], player->facingDirection);
        return id;
    }
    return OBJECT_EVENTS_COUNT;
}

static bool8 PlayerIsFast(struct ObjectEvent *player)
{
    u8 action = player->movementActionId;
    return (action >= MOVEMENT_ACTION_WALK_FAST_DOWN && action <= MOVEMENT_ACTION_WALK_FAST_RIGHT)
        || (action >= MOVEMENT_ACTION_WALK_FASTER_DOWN && action <= MOVEMENT_ACTION_WALK_FASTER_RIGHT)
        || (action >= MOVEMENT_ACTION_PLAYER_RUN_DOWN && action <= MOVEMENT_ACTION_PLAYER_RUN_RIGHT);
}

static bool8 PlayerIsJumping(struct ObjectEvent *player)
{
    return player->heldMovementActive && !player->heldMovementFinished
        && player->movementActionId >= MOVEMENT_ACTION_JUMP_2_DOWN
        && player->movementActionId <= MOVEMENT_ACTION_JUMP_2_RIGHT;
}

void StartSabrinaFollower(void)
{
    // The script sets the flag after finishing the original introduction.
    RemoveStationaryCopies();
    RemoveFollowerObjects();
    UpdateSabrinaFollower();
}

void UpdateSabrinaFollower(void)
{
    struct ObjectEvent *player;
    struct ObjectEvent *follower;
    struct FollowerStep *step;
    u8 id;
    u8 direction;
    s16 dx, dy;

    if (gPlayerAvatar.objectEventId >= OBJECT_EVENTS_COUNT)
        return;
    player = &gObjectEvents[gPlayerAvatar.objectEventId];
    if (!player->active || !player->isPlayer)
        return;
    if (!ArePlayerFieldControlsLocked())
        sFollower.talking = FALSE;
    if (ShouldSuppressFollower(player))
    {
        RemoveFollowerObjects();
        return;
    }
    RemoveStationaryCopies();
    // Connected maps rebase all engine objects, but not our runtime trail.
    if (!sFollower.ready || sFollower.mapNum != gSaveBlock1Ptr->location.mapNum
        || sFollower.mapGroup != gSaveBlock1Ptr->location.mapGroup)
    {
        RemoveFollowerObjects();
        sFollower.playerPos = player->currentCoords;
        sFollower.mapNum = gSaveBlock1Ptr->location.mapNum;
        sFollower.mapGroup = gSaveBlock1Ptr->location.mapGroup;
        sFollower.ready = TRUE;
    }
    // Ledge jumps use intermediate coordinates that are not walkable. Regroup
    // on safe land after landing rather than walking through the ledge/wall.
    if (PlayerIsJumping(player))
    {
        RemoveFollowerObjects();
        return;
    }
    id = FindFollower();
    if (id == OBJECT_EVENTS_COUNT)
    {
        id = SpawnFollower(player);
        sFollower.playerPos = player->currentCoords;
        sFollower.count = 0;
        sFollower.head = 0;
        if (id == OBJECT_EVENTS_COUNT)
            return;
    }
    follower = &gObjectEvents[id];
    // Adopt the current map identity after a seamless connection or save load.
    follower->mapNum = gSaveBlock1Ptr->location.mapNum;
    follower->mapGroup = gSaveBlock1Ptr->location.mapGroup;
    ObjectEventClearHeldMovementIfFinished(follower);
    dx = player->currentCoords.x - sFollower.playerPos.x;
    dy = player->currentCoords.y - sFollower.playerPos.y;
    if (dx != 0 || dy != 0)
    {
        if (abs(dx) + abs(dy) != 1 || sFollower.count == TRAIL_LENGTH)
        {
            RemoveFollowerObjects();
            return; // Teleport/forced displacement: recover next field frame.
        }
        step = &sFollower.steps[(sFollower.head + sFollower.count) % TRAIL_LENGTH];
        step->pos = sFollower.playerPos;
        step->fast = PlayerIsFast(player);
        sFollower.count++;
        sFollower.playerPos = player->currentCoords;
    }
    if (follower->heldMovementActive)
        return;
    // While talking, keep her in place. During Oak's scripted walks allow the
    // companion's already-accepted path, without changing script lock state.
    if (ArePlayerFieldControlsLocked()
        && (sFollower.talking || !player->heldMovementActive))
        return;
    while (sFollower.count != 0)
    {
        step = &sFollower.steps[sFollower.head];
        dx = step->pos.x - follower->currentCoords.x;
        dy = step->pos.y - follower->currentCoords.y;
        if (dx == 0 && dy == 0)
        {
            sFollower.head = (sFollower.head + 1) % TRAIL_LENGTH;
            sFollower.count--;
            continue;
        }
        if (abs(dx) + abs(dy) != 1 || !IsLandTile(step->pos.x, step->pos.y, player->currentElevation))
        {
            RemoveFollowerObjects();
            return;
        }
        if (IsOccupied(step->pos.x, step->pos.y, player))
            return;
        direction = dx < 0 ? DIR_WEST : dx > 0 ? DIR_EAST : dy < 0 ? DIR_NORTH : DIR_SOUTH;
        // Sabrina has NPC walking frames, not Red's running-frame animation.
        ObjectEventSetHeldMovement(follower, step->fast ? GetWalkFastMovementAction(direction) : GetWalkNormalMovementAction(direction));
        sFollower.head = (sFollower.head + 1) % TRAIL_LENGTH;
        sFollower.count--;
        return;
    }
}
