// Created by Oscar Eriksson in June 2022
#include "stdint.h"
#include "string.h"
#include "can.h"
#include "can_can1.h"
#include "can_hal_can1.h"
 
CAN_HandleTypeDef* _can1;
static uint32_t mailbox = 0;
 
can1_mcu_set_ecu_indicator_points_t rx_can1_mcu_set_ecu_indicator_points;
 
can1_dbu_status_1_t tx_can1_dbu_status_1;
can1_ecu_status_t tx_can1_ecu_status;
can1_potentiometer_status_t tx_can1_potentiometer_status;

void receive_callback_can_hal_can1(uint32_t FIFO) {
   CAN_RxHeaderTypeDef header;
   uint8_t data[8]; 
 
   if (HAL_OK == HAL_CAN_GetRxMessage(_can1, FIFO, &header, data)) {
       switch(header.StdId) {
           case 1292: {
               if(can1_mcu_set_ecu_indicator_points_decode(&rx_can1_mcu_set_ecu_indicator_points, data) || !CAN_VALID) {
                   if(CAN_PARTIAL || can1_mcu_set_ecu_indicator_points_counter()) {
                       can1_mcu_set_ecu_indicator_points_receive_callback(&rx_can1_mcu_set_ecu_indicator_points);
                   }
               }
           }
           break;
        }
    }
}
 
void can1_dbu_status_1_transmit() {
    uint8_t data[8] = { 0, 0, 0, 0, 0, 0, 0, 0, };
    CAN_TxHeaderTypeDef header = {
        .DLC = 8,
        .IDE = CAN_ID_STD,
        .StdId = 64,
        .RTR = CAN_RTR_DATA,
        .TransmitGlobalTime = DISABLE,
    };
 
   can1_dbu_status_1_transmit_callback(&tx_can1_dbu_status_1);
 
    can1_dbu_status_1_encode(&tx_can1_dbu_status_1, data);
    while(!HAL_CAN_GetTxMailboxesFreeLevel(_can1));
    if (HAL_CAN_AddTxMessage(_can1, &header, data, &mailbox) != HAL_OK) {
        Error_Handler();
    }
}


void can1_potentiometer_status_transmit() {
    uint8_t data[8] = { 0, 0, 0, 0, 0, 0, 0, 0, };
    CAN_TxHeaderTypeDef header = {
        .DLC = 8,
        .IDE = CAN_ID_STD,
        .StdId = 64,
        .RTR = CAN_RTR_DATA,
        .TransmitGlobalTime = DISABLE,
    };

    can1_potentiometer_status_transmit_callback(&tx_can1_potentiometer_status);
    can1_potentiometer_status_encode(&tx_can1_potentiometer_status, data);
    while (!HAL_CAN_GetTxMailboxesFreeLevel(_can1))
        ;
   if (HAL_CAN_AddTxMessage(_can1, &header, data, &mailbox) != HAL_OK)
   {
        Error_Handler();
    }
}


void can1_ecu_status_transmit() {
    uint8_t data[8] = { 0, 0, 0, 0, 0, 0, 0, 0, };
    CAN_TxHeaderTypeDef header = {
        .DLC = 8,
        .IDE = CAN_ID_STD,
        .StdId = 72,
        .RTR = CAN_RTR_DATA,
        .TransmitGlobalTime = DISABLE,
    };
 
   can1_ecu_status_transmit_callback(&tx_can1_ecu_status);
 
    can1_ecu_status_encode(&tx_can1_ecu_status, data);
    while(!HAL_CAN_GetTxMailboxesFreeLevel(_can1));
    if (HAL_CAN_AddTxMessage(_can1, &header, data, &mailbox) != HAL_OK) {
        Error_Handler();
    }
}
 
uint8_t init_peripheral_can_hal_can1(CAN_HandleTypeDef* __can1){
   _can1 = __can1;
 
   if (HAL_CAN_Start(_can1) != HAL_OK) {
       return 0;
   }
   if (HAL_CAN_WakeUp(_can1) != HAL_OK) {
       return 0;
   }
   if (HAL_CAN_ActivateNotification(_can1, CAN_IT_RX_FIFO0_MSG_PENDING | CAN_IT_RX_FIFO1_MSG_PENDING) != HAL_OK) {
       return 0;
   }
 
   return init_filter_can_hal_can1();
}
 
uint8_t init_filter_can_hal_can1(){
   CAN_FilterTypeDef filter_config;
   filter_config.FilterActivation = ENABLE;
   filter_config.FilterScale = CAN_FILTERSCALE_16BIT;
 
   filter_config.FilterMode = CAN_FILTERMODE_IDMASK;
   filter_config.FilterBank = filter_counter++;
   filter_config.FilterMaskIdHigh = (0xffff << 5) & 0xffff;
   filter_config.FilterIdHigh = (0x050c << 5) & 0xffff;
   filter_config.FilterMaskIdLow = (0xffff << 5) & 0xffff;
   filter_config.FilterIdLow = (0x0000 << 5) & 0xffff;
 
   filter_config.FilterFIFOAssignment = CAN_FILTER_FIFO0;
   if (HAL_CAN_ConfigFilter(_can1, &filter_config) != HAL_OK) return 0;
   filter_config.FilterFIFOAssignment = CAN_FILTER_FIFO1;
   if (HAL_CAN_ConfigFilter(_can1, &filter_config) != HAL_OK) return 0;
 
   return 1;
}
 
uint8_t can1_mcu_set_ecu_indicator_points_counter() {
    return 1;
}
 