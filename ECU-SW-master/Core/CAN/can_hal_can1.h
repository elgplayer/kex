// Created by Oscar Eriksson in June 2022
#ifndef _CAN_HAL_CAN1_
#define _CAN_HAL_CAN1_
 
 
#include "stdint.h"
#include "string.h"
#include "can.h"
#include "kthfspe_can.h"
#include "can_can1.h"
//#include "can_hal_can1.h"
 
extern CAN_HandleTypeDef* _can1;
 
void receive_callback_can_hal_can1(uint32_t);
 
uint8_t init_peripheral_can_hal_can1(CAN_HandleTypeDef*);
 
uint8_t init_filter_can_hal_can1();
 
uint8_t can1_mcu_set_ecu_indicator_points_counter();
 
 
#endif
