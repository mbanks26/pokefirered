@ Additive dialogue; all starter, healing, battle and reward mechanics stay native.
Family_EventScript_MomBeforeJourney::
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	special HoldSabrinaForConversation
	msgbox Family_Text_MomSabrina
	return

Family_EventScript_MomMilestone::
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	special HoldSabrinaForConversation
	goto_if_set FLAG_SYS_GAME_CLEAR, Family_EventScript_MomChampion
	goto_if_set FLAG_BADGE08_GET, Family_EventScript_MomEightBadges
	goto_if_set FLAG_LEAF_VIRIDIAN_REUNION, Family_EventScript_MomLeafNews
	msgbox Family_Text_MomSabrina
	return

Family_EventScript_MomLeafNews::
	msgbox Family_Text_MomLeafNews
	return

Family_EventScript_MomEightBadges::
	msgbox Family_Text_MomEightBadges
	return

Family_EventScript_MomChampion::
	msgbox Family_Text_MomChampion
	return

Family_EventScript_OakStarters::
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	msgbox Family_Text_OakStarters
	return

Family_EventScript_OakPokedex::
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	msgbox Family_Text_OakPokedex
	return

Family_EventScript_BlueFirstBattle::
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	msgbox Family_Text_BlueFirstBattle
	return

Family_EventScript_Brock::
	goto_if_unset FLAG_LEAF_VIRIDIAN_REUNION, EventScript_Return
	goto_if_set FLAG_BADGE01_GET, EventScript_Return
	msgbox Family_Text_Brock
	return

Family_EventScript_Misty::
	goto_if_unset FLAG_LEAF_VIRIDIAN_REUNION, EventScript_Return
	goto_if_set FLAG_BADGE02_GET, EventScript_Return
	msgbox Family_Text_Misty
	return

Family_EventScript_SabrinaGymChallenge::
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	goto_if_set FLAG_BADGE06_GET, EventScript_Return
	msgbox Family_Text_SabrinaGymChallenge
	return

Family_EventScript_Erika::
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	goto_if_set FLAG_BADGE04_GET, EventScript_Return
	msgbox Family_Text_Erika
	return

Family_EventScript_Giovanni::
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, EventScript_Return
	msgbox Family_Text_Giovanni
	return
