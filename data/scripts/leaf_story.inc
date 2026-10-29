@ Leaf's first appearance. Only the southern Route 1 entrance triggers this.
Leaf_EventScript_ViridianReunion::
	setvar VAR_TEMP_F, 1
	goto_if_questlog Leaf_EventScript_End
	goto_if_set FLAG_LEAF_VIRIDIAN_REUNION, Leaf_EventScript_End
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, Leaf_EventScript_End
	goto_if_unset FLAG_SABRINA_FOLLOWER_ACTIVE, Leaf_EventScript_End
	special GetPlayerXY
	goto_if_lt VAR_0x8004, 22, Leaf_EventScript_End
	goto_if_gt VAR_0x8004, 25, Leaf_EventScript_End
	goto_if_lt VAR_0x8005, 38, Leaf_EventScript_End
	specialvar VAR_RESULT, GetPlayerFacingDirection
	goto_if_ne VAR_RESULT, DIR_NORTH, Leaf_EventScript_End
	lockall
	setvar VAR_TEMP_F, 1
	special QuestLog_CutRecording
	turnobject LOCALID_PLAYER, DIR_NORTH
	special StageSabrinaForLeafScene
	special GetPlayerXY
	subvar VAR_0x8005, 3
	setobjectxyperm LOCALID_VIRIDIAN_LEAF, VAR_0x8004, VAR_0x8005
	clearflag FLAG_HIDE_VIRIDIAN_LEAF
	addobject LOCALID_VIRIDIAN_LEAF
	textcolor NPC_TEXT_COLOR_FEMALE
	msgbox Leaf_Text_ViridianCall
	closemessage
	applymovement LOCALID_VIRIDIAN_LEAF, Leaf_Movement_Approach
	waitmovement 0
	msgbox Leaf_Text_ViridianGreeting
	msgbox Leaf_Text_ViridianSabrina
	msgbox Leaf_Text_ViridianSabrinaReply
	msgbox Leaf_Text_ViridianBadges
	msgbox Leaf_Text_ViridianEevee
	msgbox Leaf_Text_ViridianFarewell
	msgbox Leaf_Text_ViridianSabrinaFarewell
	closemessage
	applymovement LOCALID_VIRIDIAN_LEAF, Leaf_Movement_Depart
	waitmovement 0
	removeobject LOCALID_VIRIDIAN_LEAF
	setflag FLAG_HIDE_VIRIDIAN_LEAF
	setflag FLAG_LEAF_VIRIDIAN_REUNION
	special EndSabrinaLeafScene
	releaseall
	end

Leaf_EventScript_End::
	releaseall
	end

Leaf_Movement_Approach::
	walk_down
	walk_down
	step_end

Leaf_Movement_Depart::
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	walk_up
	step_end
