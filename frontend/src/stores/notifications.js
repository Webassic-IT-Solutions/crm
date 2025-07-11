import { defineStore } from 'pinia'
import { createResource } from 'frappe-ui'
import { computed, ref, watch } from 'vue'

export const visible = ref(false)

export const current_page = ref(1)

export const notificationsResource = createResource({
  url: 'crm.api.notifications.get_notifications',
  params: {
    page_number: current_page.value
  },
  makeParams() {
    return {
      page_number: current_page.value
    }
  },
  initialData: [],
  auto: true,
  onSuccess: () => {
    console.log(notificationsResource)
    
  }
})

export const notifications = computed(
  () => notificationsResource.data
)

export const unreadNotificationsCount = computed(
  () => notificationsResource.data.unread_count || 0,
)

export const notificationsStore = defineStore('crm-notifications', () => {
  const mark_as_read = createResource({
    url: 'crm.api.notifications.mark_as_read',
    onSuccess: () => {
      mark_as_read.params = {}
      notificationsResource.reload()
    },
  })

  function toggle() {
    visible.value = !visible.value
  }

  function mark_doc_as_read(doc) {
    mark_as_read.params = { doc: doc }
    mark_as_read.reload()
    //toggle()
  }
  function load_next_page(){
    let offset  = (current_page.value) * 20
    if( offset <= notificationsResource.data.total_count){
      current_page.value += 1
    }
  }
  function has_more() {
    console.log("has_more")
    let offset  = (current_page.value) * 20;
    return offset <= notificationsResource.data.total_count;
  }
  function reset(){
    current_page.value = 1
  }
  watch(current_page, ()=>{
    notificationsResource.reload()
  })

  return {
    unreadNotificationsCount,
    mark_as_read,
    mark_doc_as_read,
    toggle,
    load_next_page,
    has_more,
    reset,
  }
})
