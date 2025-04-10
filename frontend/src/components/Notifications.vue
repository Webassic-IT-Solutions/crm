<template>
  <div
    v-if="visible"
    ref="target"
    class="absolute z-20 h-screen bg-surface-white transition-all duration-300 ease-in-out"
    :style="{
      'box-shadow': '8px 0px 8px rgba(0, 0, 0, 0.1)',
      'max-width': '350px',
      'min-width': '350px',
      left: 'calc(100% + 1px)',
    }"
  >
    <div class="flex h-screen flex-col text-ink-gray-9">
      <div
        class="z-20 flex items-center justify-between border-b bg-surface-white px-5 py-2.5"
      >
        <div class="text-base font-medium">{{ __('Notifications') }}</div>
        <div class="flex gap-1">
          <Tooltip :text="__('Mark all as read')">
            <div>
              <Button variant="ghost" @click="() => markAllAsRead()">
                <template #icon>
                  <MarkAsDoneIcon class="h-4 w-4" />
                </template>
              </Button>
            </div>
          </Tooltip>
          <Tooltip :text="__('Close')">
            <div>
              <Button variant="ghost" @click="() => toggle()">
                <template #icon>
                  <FeatherIcon name="x" class="h-4 w-4" />
                </template>
              </Button>
            </div>
          </Tooltip>
        </div>
      </div>
      <div
        v-if="notifications.data?.length"
        class="divide-y divide-outline-gray-modals overflow-auto text-base"
      >
        <RouterLink
          v-for="n in notifications.data"
          :key="n.comment"
          :to="getRoute(n)"
          class="flex cursor-pointer items-start gap-2.5 px-4 py-2.5 hover:bg-surface-gray-2"
          @click="markAsRead(n.comment || n.notification_type_doc)"
        >
          <div class="mt-1 flex items-center gap-2.5">
            <div
              class="size-[5px] rounded-full"
              :class="[n.read ? 'bg-transparent' : 'bg-surface-gray-7']"
            />
            <WhatsAppIcon v-if="n.type == 'WhatsApp'" class="size-7" />
            <UserAvatar v-else :user="n.from_user.name" size="lg" />
          </div>
          <div>
            <div v-if="n.notification_text" v-html="n.notification_text" />
            <div v-else class="mb-2 space-x-1 leading-5 text-ink-gray-5">
              <span class="font-medium text-ink-gray-9">
                {{ n.from_user.full_name }}
              </span>
              <span>
                {{ __('mentioned you in {0}', [n.reference_doctype]) }}
              </span>
              <span class="font-medium text-ink-gray-9">
                {{ n.reference_name }}
              </span>
            </div>
            <div class="text-sm text-ink-gray-5">
              {{ __(timeAgo(n.creation)) }}
            </div>
          </div>
        </RouterLink>
      </div>
      <div
        v-else
        class="flex flex-1 flex-col items-center justify-center gap-2"
      >
        <NotificationsIcon class="h-20 w-20 text-ink-gray-2" />
        <div class="text-lg font-medium text-ink-gray-4">
          {{ __('No new notifications') }}
        </div>
      </div>
    </div>
  </div>
  <!-- In-app Popup -->
  <Transition name="fade">
    <div
      v-if="showPopup"
      class="fixed bottom-5 right-5 z-50 max-w-sm rounded-lg bg-white p-4 shadow-lg border border-gray-200"
    >
      <div class="flex items-start gap-3">
        <UserAvatar v-if="popupNotification" :user="popupNotification.from_user?.name || ''" size="md" />
        <div>
          <div class="text-sm font-medium">{{ popupNotification?.from_user?.full_name || 'Someone' }}</div>
          <div class="text-sm text-gray-700" v-html="popupNotification?.notification_text" />
        </div>
      </div>
    </div>
  </Transition>

  <!-- Audio element for notification sound -->
  <audio ref="notificationSound" src="/notification.mp3" preload="auto" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { onClickOutside } from '@vueuse/core'
import { capture } from '@/telemetry'
import { Tooltip } from 'frappe-ui'
import WhatsAppIcon from '@/components/Icons/WhatsAppIcon.vue'
import MarkAsDoneIcon from '@/components/Icons/MarkAsDoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import {
  visible,
  notifications,
  notificationsStore,
} from '@/stores/notifications'
import { globalStore } from '@/stores/global'
import { timeAgo } from '@/utils'

const { $socket } = globalStore()
const { mark_as_read, toggle, mark_doc_as_read } = notificationsStore()
const target = ref(null)
onClickOutside(
  target,
  () => {
    if (visible.value) toggle()
  },
  {
    ignore: ['#notifications-btn'],
  },
)

const showPopup = ref(false)
const popupNotification = ref(null)
const notificationPermission = ref(Notification.permission)
const notificationSound = ref(null)

function requestNotificationPermission() {
  if (!("Notification" in window)) {
    console.warn("This browser does not support desktop notifications.")
    return
  }

  Notification.requestPermission().then(permission => {
    console.log("Notification permission:", permission)
    notificationPermission.value = permission

    if (permission === "granted") {
      new Notification("🎉 Notifications Enabled!", {
        icon: "/notification-icon.png",
        tag: "frappe-notification"
      })
    }
  })
}

function playNotificationSound() {
  if (notificationSound.value) {
    notificationSound.value.currentTime = 0
    notificationSound.value.play().catch(err => {
      console.warn('Sound playback failed:', err)
    })
  }
}

function showPushNotification(notification) {
  console.log("Notification received:", notification)

  if (notificationPermission.value === 'granted') {
    playNotificationSound()
    new Notification(notification.title || 'New Notification', {
      body: notification.message || notification.notification_text || 'You have a new notification',
      icon: '/notification-icon.png',
      tag: notification.notification_type_doc,
    })
    return
  }

  if (notificationPermission.value === 'default') {
    Notification.requestPermission().then(permission => {
      notificationPermission.value = permission
      if (permission === 'granted') {
        showPushNotification(notification)
      } else {
        showInAppPopup(notification)
      }
    })
  } else {
    showInAppPopup(notification)
  }
}

function showInAppPopup(notification) {
  console.log("In-app popup notification:", notification)
  playNotificationSound()
  popupNotification.value = notification
  showPopup.value = true
  setTimeout(() => (showPopup.value = false), 30000)
}

function markAsRead(doc) {
  capture('notification_mark_as_read')
  mark_doc_as_read(doc)
}

function markAllAsRead() {
  capture('notification_mark_all_as_read')
  mark_as_read.reload()
}

onBeforeUnmount(() => {
  $socket.off('crm_notification')
})

onMounted(() => {
  $socket.on('crm_notification', (notification) => {
    notifications.reload()
    showPushNotification(notification)
  })
})

function getRoute(notification) {
  if(!notification.reference_name){
    return {
      name: "Tasks"
    }

  }
  let params = {
    leadId: notification.reference_name,
  }
  if (notification.route_name === 'Deal') {
    params = {
      dealId: notification.reference_name,
    }
  }

  return {
    name: notification.route_name,
    params: params,
    hash: notification.hash,
  }
}
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>