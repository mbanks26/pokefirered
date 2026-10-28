@ Sabrina joins after her first Pallet conversation. Later conversations only
@ read story flags; they never advance Oak's, Blue's, or the Gym story scripts.
@ MSGBOX_NPC handles locking, facing the player, and releasing for each branch.

Sabrina_EventScript_PalletTown::
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, Sabrina_EventScript_Join
	goto_if_set FLAG_SYS_GAME_CLEAR, Sabrina_EventScript_PalletChampion
	goto_if_set FLAG_BADGE08_GET, Sabrina_EventScript_PalletEightBadges
	goto_if_set FLAG_BADGE06_GET, Sabrina_EventScript_PalletMarshBadge
	goto_if_set FLAG_BADGE01_GET, Sabrina_EventScript_PalletFirstBadge
	goto_if_set FLAG_SYS_POKEMON_GET, Sabrina_EventScript_PalletPartner
	msgbox Sabrina_Text_PalletIntro, MSGBOX_NPC
	end

Sabrina_EventScript_Join::
	lock
	faceplayer
	goto_if_set FLAG_SYS_POKEMON_GET, Sabrina_EventScript_JoinDuringJourney
	msgbox Sabrina_Text_PalletIntro
	goto Sabrina_EventScript_StartCompanion

Sabrina_EventScript_JoinDuringJourney::
	msgbox Sabrina_Text_JoinDuringJourney

Sabrina_EventScript_StartCompanion::
	msgbox Sabrina_Text_JoinCompanion
	closemessage
	setflag FLAG_SABRINA_FOLLOWER_ACTIVE
	special StartSabrinaFollower
	release
	end

Sabrina_EventScript_PalletChampion::
	msgbox Sabrina_Text_PalletChampion, MSGBOX_NPC
	end

Sabrina_EventScript_PalletEightBadges::
	msgbox Sabrina_Text_PalletEightBadges, MSGBOX_NPC
	end

Sabrina_EventScript_PalletMarshBadge::
	msgbox Sabrina_Text_PalletMarshBadge, MSGBOX_NPC
	end

Sabrina_EventScript_PalletFirstBadge::
	msgbox Sabrina_Text_PalletFirstBadge, MSGBOX_NPC
	end

Sabrina_EventScript_PalletPartner::
	msgbox Sabrina_Text_PalletPartner, MSGBOX_NPC
	end

Sabrina_EventScript_ViridianCity::
	goto_if_set FLAG_BADGE08_GET, Sabrina_EventScript_ViridianAfterGym
	msgbox Sabrina_Text_ViridianBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_ViridianAfterGym::
	msgbox Sabrina_Text_ViridianAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_PewterCity::
	goto_if_set FLAG_BADGE01_GET, Sabrina_EventScript_PewterAfterGym
	msgbox Sabrina_Text_PewterBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_PewterAfterGym::
	msgbox Sabrina_Text_PewterAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_CeruleanCity::
	goto_if_set FLAG_BADGE02_GET, Sabrina_EventScript_CeruleanAfterGym
	goto_if_set FLAG_GOT_SS_TICKET, Sabrina_EventScript_CeruleanBill
	msgbox Sabrina_Text_CeruleanBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_CeruleanAfterGym::
	msgbox Sabrina_Text_CeruleanAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_CeruleanBill::
	msgbox Sabrina_Text_CeruleanBill, MSGBOX_NPC
	end

Sabrina_EventScript_VermilionCity::
	goto_if_set FLAG_BADGE03_GET, Sabrina_EventScript_VermilionAfterGym
	goto_if_set FLAG_GOT_HM01, Sabrina_EventScript_VermilionBeforeGym
	msgbox Sabrina_Text_VermilionBeforeCut, MSGBOX_NPC
	end

Sabrina_EventScript_VermilionAfterGym::
	msgbox Sabrina_Text_VermilionAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_VermilionBeforeGym::
	msgbox Sabrina_Text_VermilionBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_LavenderTown::
	goto_if_set FLAG_RESCUED_MR_FUJI, Sabrina_EventScript_LavenderAfterRescue
	msgbox Sabrina_Text_LavenderBeforeRescue, MSGBOX_NPC
	end

Sabrina_EventScript_LavenderAfterRescue::
	msgbox Sabrina_Text_LavenderAfterRescue, MSGBOX_NPC
	end

Sabrina_EventScript_FuchsiaCity_PokemonCenter_1F::
	goto_if_set FLAG_BADGE05_GET, Sabrina_EventScript_FuchsiaAfterGym
	msgbox Sabrina_Text_FuchsiaBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_FuchsiaAfterGym::
	msgbox Sabrina_Text_FuchsiaAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_SaffronCity::
	goto_if_set FLAG_BADGE06_GET, Sabrina_EventScript_SaffronAfterGym
	goto_if_set FLAG_HIDE_SAFFRON_ROCKETS, Sabrina_EventScript_SaffronFreed
	msgbox Sabrina_Text_SaffronRockets, MSGBOX_NPC
	end

Sabrina_EventScript_SaffronAfterGym::
	msgbox Sabrina_Text_SaffronAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_SaffronFreed::
	msgbox Sabrina_Text_SaffronFreed, MSGBOX_NPC
	end

Sabrina_EventScript_CinnabarIsland::
	goto_if_set FLAG_BADGE07_GET, Sabrina_EventScript_CinnabarAfterGym
	msgbox Sabrina_Text_CinnabarBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_CinnabarAfterGym::
	msgbox Sabrina_Text_CinnabarAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_IndigoPlateau_PokemonCenter_1F::
	goto_if_set FLAG_SYS_GAME_CLEAR, Sabrina_EventScript_LeagueChampion
	msgbox Sabrina_Text_LeagueBeforeChallenge, MSGBOX_NPC
	end

Sabrina_EventScript_LeagueChampion::
	msgbox Sabrina_Text_LeagueChampion, MSGBOX_NPC
	end

Sabrina_EventScript_OneIsland::
	goto_if_set FLAG_RESCUED_LOSTELLE, Sabrina_EventScript_OneIslandAfterRescue
	goto_if_set FLAG_SYS_GAME_CLEAR, Sabrina_EventScript_OneIslandPostgame
	msgbox Sabrina_Text_OneIslandBeforeRescue, MSGBOX_NPC
	end

Sabrina_EventScript_OneIslandAfterRescue::
	msgbox Sabrina_Text_OneIslandAfterRescue, MSGBOX_NPC
	end

Sabrina_EventScript_OneIslandPostgame::
	msgbox Sabrina_Text_OneIslandPostgame, MSGBOX_NPC
	end

Sabrina_EventScript_CeladonCity::
	goto_if_set FLAG_HIDE_CELADON_ROCKETS, Sabrina_EventScript_CeladonRockets
	goto_if_set FLAG_BADGE04_GET, Sabrina_EventScript_CeladonAfterGym
	msgbox Sabrina_Text_CeladonBeforeGym, MSGBOX_NPC
	end

Sabrina_EventScript_CeladonRockets::
	goto_if_set FLAG_BADGE04_GET, Sabrina_EventScript_CeladonAfterGymRockets
	msgbox Sabrina_Text_CeladonRockets, MSGBOX_NPC
	end

Sabrina_EventScript_CeladonAfterGym::
	msgbox Sabrina_Text_CeladonAfterGym, MSGBOX_NPC
	end

Sabrina_EventScript_CeladonAfterGymRockets::
	msgbox Sabrina_Text_CeladonAfterGymRockets, MSGBOX_NPC
	end

@ Used on routes and in interiors without a location-specific conversation.
Sabrina_EventScript_Companion::
	goto_if_set FLAG_SYS_GAME_CLEAR, Sabrina_EventScript_CompanionChampion
	goto_if_set FLAG_BADGE08_GET, Sabrina_EventScript_CompanionEightBadges
	goto_if_set FLAG_BADGE06_GET, Sabrina_EventScript_CompanionMarshBadge
	goto_if_set FLAG_BADGE01_GET, Sabrina_EventScript_CompanionFirstBadge
	goto_if_set FLAG_SYS_POKEMON_GET, Sabrina_EventScript_CompanionJourney
	msgbox Sabrina_Text_CompanionBeforeStarter, MSGBOX_NPC
	end

Sabrina_EventScript_CompanionJourney::
	msgbox Sabrina_Text_CompanionJourney, MSGBOX_NPC
	end

Sabrina_EventScript_CompanionFirstBadge::
	msgbox Sabrina_Text_CompanionFirstBadge, MSGBOX_NPC
	end

Sabrina_EventScript_CompanionMarshBadge::
	msgbox Sabrina_Text_CompanionMarshBadge, MSGBOX_NPC
	end

Sabrina_EventScript_CompanionEightBadges::
	msgbox Sabrina_Text_CompanionEightBadges, MSGBOX_NPC
	end

Sabrina_EventScript_CompanionChampion::
	msgbox Sabrina_Text_CompanionChampion, MSGBOX_NPC
	end
