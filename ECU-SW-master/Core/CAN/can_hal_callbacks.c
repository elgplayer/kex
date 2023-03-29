#include "kthfspe_can.h"
 
void HAL_CAN_RxFifo0MsgPendingCallback(CAN_HandleTypeDef *hcan) {
   if(hcan == _can1) {
       receive_callback_can_hal_can1(CAN_RX_FIFO0);
   }
 
}
 
void HAL_CAN_RxFifo1MsgPendingCallback(CAN_HandleTypeDef *hcan) {
   if(hcan == _can1) {
       receive_callback_can_hal_can1(CAN_RX_FIFO1);
   }
 
}
 