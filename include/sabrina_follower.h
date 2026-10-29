#ifndef GUARD_SABRINA_FOLLOWER_H
#define GUARD_SABRINA_FOLLOWER_H

// An overworld companion, never a party member. No save-layout changes.
void StartSabrinaFollower(void);
void UpdateSabrinaFollower(void);
void StageSabrinaForLeafScene(void);
void EndSabrinaLeafScene(void);
void HoldSabrinaForConversation(void);
bool8 IsSabrinaFollower(const struct ObjectEvent *objectEvent);
const u8 *GetSabrinaFollowerScript(void);
const struct ObjectEventTemplate *GetSabrinaFollowerTemplate(void);

#endif
