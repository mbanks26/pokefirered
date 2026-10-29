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

@ Each town recomputes visibility on entry, including older cartridge saves.
Leaf_EventScript_SetCeruleanVisibility::
	setflag FLAG_HIDE_LATER_LEAF
	goto_if_unset FLAG_LEAF_VIRIDIAN_REUNION, EventScript_Return
	goto_if_set FLAG_LEAF_LEFT_CERULEAN, EventScript_Return
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	clearflag FLAG_HIDE_LATER_LEAF
	return

Leaf_EventScript_SetLavenderVisibility::
	setflag FLAG_HIDE_LATER_LEAF
	goto_if_unset FLAG_LEAF_VIRIDIAN_REUNION, EventScript_Return
	goto_if_set FLAG_LEAF_EEVEE_EVOLVED, EventScript_Return
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	clearflag FLAG_HIDE_LATER_LEAF
	return

Leaf_EventScript_SetSaffronVisibility::
	setflag FLAG_HIDE_LATER_LEAF
	goto_if_unset FLAG_LEAF_VIRIDIAN_REUNION, EventScript_Return
	goto_if_unset FLAG_RESCUED_MR_FUJI, EventScript_Return
	checkplayergender
	goto_if_ne VAR_RESULT, MALE, EventScript_Return
	clearflag FLAG_HIDE_LATER_LEAF
	return

Leaf_EventScript_Cerulean::
	lock
	faceplayer
	special HoldSabrinaForConversation
	textcolor NPC_TEXT_COLOR_FEMALE
	msgbox Leaf_Text_Cerulean
	msgbox Leaf_Text_CeruleanSabrina
	release
	end

Leaf_EventScript_Lavender::
	lock
	faceplayer
	special HoldSabrinaForConversation
	textcolor NPC_TEXT_COLOR_FEMALE
	setflag FLAG_LEAF_LEFT_CERULEAN
	goto_if_set FLAG_RESCUED_MR_FUJI, Leaf_EventScript_LavenderSafe
	msgbox Leaf_Text_Lavender
	msgbox Leaf_Text_LavenderSabrina
	release
	end

Leaf_EventScript_LavenderSafe::
	msgbox Leaf_Text_LavenderSafe
	release
	end

Leaf_EventScript_Saffron::
	setflag FLAG_LEAF_LEFT_CERULEAN
	lock
	faceplayer
	special HoldSabrinaForConversation
	textcolor NPC_TEXT_COLOR_FEMALE
	goto_if_set FLAG_LEAF_EEVEE_EVOLVED, Leaf_EventScript_SaffronVaporeon
	goto_if_set FLAG_HIDE_SAFFRON_ROCKETS, Leaf_EventScript_EeveeEvolution
	msgbox Leaf_Text_SaffronRockets
	msgbox Leaf_Text_SaffronSabrina
	release
	end

Leaf_EventScript_EeveeEvolution::
	msgbox Leaf_Text_WaterStone
	closemessage
	showmonpic SPECIES_EEVEE, 10, 3
	playmoncry SPECIES_EEVEE, 0
	msgbox Leaf_Text_EeveeChoice
	closemessage
	waitmoncry
	hidemonpic
	delay 30
	showmonpic SPECIES_VAPOREON, 10, 3
	playfanfare MUS_LEVEL_UP
	playmoncry SPECIES_VAPOREON, 0
	msgbox Leaf_Text_Vaporeon
	closemessage
	waitfanfare
	waitmoncry
	hidemonpic
	setflag FLAG_LEAF_EEVEE_EVOLVED
	release
	end

Leaf_EventScript_SaffronVaporeon::
	msgbox Leaf_Text_SaffronVaporeon
	release
	end
