import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useCallStore = defineStore('call', ()=>{
 
    const callStatus = ref('Waiting')
    function updateCallState(status) {
        callStatus.value = status
    }
    return {callStatus, updateCallState}
})