// Copyright (c) rAthena Dev Teams - Licensed under GNU GPL
// For more information, see LICENCE in the main folder

/**
 * Custom Atcommands
 * Place the body of custom atcommands in this file.
 * Format:
 *	ACMD_FUNC(command_name)
 *	{
 *		<code>;
 *	}
 **/

//ACMD_FUNC(newcommand)
//{
//	clif_displaymessage(fd, "It works!");
//	clif_specialeffect(&sd->bl, EF_HEARTCASTING, AREA);
//	return 0;
//}

ACMD_FUNC(bank)
{
	if (!battle_config.feature_banking || map_getmapflag(sd->m, MF_NOBANK)) {
		clif_displaymessage(fd, "Banking is unavailable here.");
		return -1;
	}
	sd->state.banking = 1;
	clif_bank_open(*sd);
	return 0;
}
