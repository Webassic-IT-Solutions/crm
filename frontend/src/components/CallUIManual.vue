<template>
    <div v-bind="$attrs">
        <div ref="callPopup"
            class="fixed z-20 flex w-60 cursor-move select-none flex-col rounded-lg bg-surface-gray-7 p-4 text-ink-gray-2 shadow-2xl"
            :style="style">

            <div class="flex flex-row-reverse items-center gap-1">
                <MinimizeIcon class="h-4 w-4 cursor-pointer" @click="toggleCallWindow" />
            </div>

            <div class="flex flex-col items-center justify-center gap-3">
                <Avatar :image="props.reference_doc?.lead_name.image" :label="props.reference_doc?.lead_name"
                    class="relative flex !h-24 !w-24 items-center justify-center [&>div]:text-[30px]"
                    :class="onCall || calling ? '' : 'pulse'" />
                <div class="flex flex-col items-center justify-center gap-1">
                    <div class="text-xl font-medium">
                        {{ props.reference_doc?.lead_name }}
                    </div>
                    <div class="text-sm text-ink-gray-5">{{ props.reference_doc?.mobile_no }}</div>
                </div>
                <CountUpTimer ref="counterUp">
                    <div>{{ counterUp?.updatedTime }}</div>
                </CountUpTimer>


                <div v-if="onCall" class="flex gap-2">

                    <div class="flex flex-col gap-4">
                    <Button v-if="onCall"  size="md"  variant="solid" theme="red" >
                            <template #icon>
                                <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" @click.stop="hangUpCall"/>
                                
                            </template>
                        </Button>
                        </div>
                </div>

                <div v-if="calling" class="flex gap-2">
                    <Button size="md" variant="solid" theme="green" :label="__('Accepted')" class="rounded-lg"
                        @click="acceptCall">
                        <template #prefix>
                            <PhoneIcon class="h-4 w-4 fill-white" />
                        </template>
                    </Button>
                    <Button size="md" variant="solid" theme="red" :label="__('Rejected')" class="rounded-lg"
                        @click="rejectCall">
                        <template #prefix>
                            <PhoneIcon class="h-4 w-4 rotate-[135deg] fill-white" />
                        </template>
                    </Button>
                </div>
                <div v-if="completeCall" class="flex gap-2">
                    <div class="flex flex-col gap-4">
                        <div>
                            <FormControl ref="title" :label="__('Title')" v-model="_note.title"
                                :placeholder="__('Call with John Doe')" />
                        </div>
                        <div>
                            <div class="mb-1.5 text-xs text-ink-gray-5">{{ __('Content') }}</div>
                            <TextEditor variant="outline" ref="content"
                                editor-class="!prose-sm overflow-auto min-h-40 max-h-40 py-1.5 px-2 rounded border border-[--surface-gray-2] bg-surface-gray-2 placeholder-ink-gray-4 hover:border-outline-gray-modals hover:bg-surface-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-2 focus-visible:ring-outline-gray-3 text-ink-gray-8 transition-colors"
                                :bubbleMenu="true" :content="_note.content" @change="(val) => (_note.content = val)"
                                :placeholder="__('Took a call with John Doe and discussed the new project.')
                                    " />

                        </div>
                        <div>
                            <FormControl  :label="__('Duration')" v-model="_note.duration" />
                        </div>
                        <Button size="md" variant="solid" theme="green" :label="__('Add Note')" class="rounded-lg"  @click.stop="saveCallLog">
                            <template #prefix>
                                <NoteIcon class="h-4 w-4 fill-white" />
                            </template>
                        </Button>
                    </div>

                </div>

            </div>
        </div>
    </div>

</template>

<script setup>

import { useDraggable, useWindowSize } from '@vueuse/core'
import { ref } from 'vue';
import { Avatar, call , dayjs} from 'frappe-ui'
import { TextEditor } from 'frappe-ui'

import MinimizeIcon from '@/components/Icons/MinimizeIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import CountUpTimer from '@/components/CountUpTimer.vue'
import { usersStore } from '../stores/users';
import { useCallStore } from '../stores/call';
import { hmsToSeconds } from '../utils';

const props = defineProps({
  reference_doc: {
    type: Object,
    default: null,
  },
})
const emit = defineEmits(['after'])

const { getUser } = usersStore()

const { callStatus, updateCallState} = useCallStore();


let callPopup = ref(null)
let counterUp = ref(null)

let onCall = ref(false)
let calling = ref(true)
let completeCall = ref(false)
let _note = ref({ title: "Call Log" })
let startTime = null
let endTime = null

function acceptCall() {
    counterUp && counterUp.value.start();
    startTime = new Date();
    onCall.value = true;
    calling.value = false;
    completeCall.value = false
    updateCallState("OnCall")
    _note.value = { title: "Call Accepted", content: "Call on number #" + props.reference_doc?.mobile_no + " accepted", call_status: "Accepted" }

}
function hangUpCall(){
    let duration = counterUp.value.stop()
    _note.value = {..._note.value, duration}
    completeCall.value = true
    calling.value = false;
    onCall.value = false;
    endTime = new Date();

    updateCallState("Completed")
    console.log(callDuration);

}
function rejectCall() {
    completeCall.value = true
    startTime = new Date();
    endTime = new Date();
    onCall.value = false;
    calling.value = true;

    updateCallState("No Answer")
    _note.value = { title: "Call Rejected", content: "Call on number #" + props.reference_doc?.mobile_no + " rejected" , call_status: "Rejected", duration:0}
}
async function saveCallLog(){
    console.log(props.reference_doc)
    console.log(_note.value)
    let note = await call('frappe.client.insert', {
      doc: {
        doctype: 'FCRM Note',
            title: _note.value.title,
            content: _note.value.content,
            reference_doctype: props.reference_doc.doctype,
            reference_docname: props.reference_doc.name || '',
      },
    })

    let callLog = await call('frappe.client.insert', {
        doc: {
            id: note.name,
            doctype: 'CRM Call Log',
            type:"Outgoing",
            from: getUser().mobile_no,
            to: props.reference_doc.mobile_no,
            caller: getUser().email,
            start_time: dayjs(startTime).format("YYYY-MM-DD HH:mm:ss"),
            end_time: dayjs(endTime).format("YYYY-MM-DD HH:mm:ss"),
            duration: hmsToSeconds(_note.value.duration || "0:00"),
            medium:"Phone",
            status: _note.value.call_status==="Rejected"? "No Answer": "Completed",
            reference_doctype: props.reference_doc.doctype,
            reference_docname: props.reference_doc.name || '',
            note: note.name,
      },
    })

    if (note.name) {
      emit('after', callLog, true)
    }
    onCall.value = false;
    calling.value = true;
    completeCall.value = false

    updateCallState("Call Added")

}
const { width, height } = useWindowSize()
const toggleCallWindow = () => { }
let { style } = useDraggable(callPopup, {
    initialValue: { x: width.value - 580, y: height.value - 710 },
    preventDefault: true,
})


</script>
<style scoped>
.pulse::before {
    content: '';
    position: absolute;
    border: 1px solid green;
    width: calc(100% + 20px);
    height: calc(100% + 20px);
    border-radius: 50%;
    animation: pulse 1s linear infinite;
}

.pulse::after {
    content: '';
    position: absolute;
    border: 1px solid green;
    width: calc(100% + 20px);
    height: calc(100% + 20px);
    border-radius: 50%;
    animation: pulse 1s linear infinite;
    animation-delay: 0.3s;
}

@keyframes pulse {
    0% {
        transform: scale(0.5);
        opacity: 0;
    }

    50% {
        transform: scale(1);
        opacity: 1;
    }

    100% {
        transform: scale(1.3);
        opacity: 0;
    }
}
</style>