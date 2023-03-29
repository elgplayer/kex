// Created by Oscar Eriksson in June 2022
#ifndef _KTHFS_CAN_
#define _KTHFS_CAN_
 
 /* CAN_VALID : received callback is not triggered if invalid (out of bounds) data is gathered */
#define CAN_VALID 0
 /* CAN_REWIND : received callback is triggered when every multiplex component is received */
#define CAN_REWIND 1
 /* CAN_PARTIAL : received callback will trigger even if some multiplex components are invalid */
#define CAN_PARTIAL 1
 
 
#include "stdint.h"
#include "string.h"
#include "can.h"
#include "can_hal_can1.h"
uint16_t filter_counter;
 
#endif