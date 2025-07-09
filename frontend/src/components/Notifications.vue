<template>
  <div
    ref="target"
    class="h-full flex flex-col bg-surface-white transition-all duration-300 ease-in-out"
  >
    <!-- Header -->
    <div class="z-20 flex items-center justify-between border-b bg-surface-white px-5 py-2.5">
      <div class="text-base font-medium">{{ __('Notifications') }}</div>
      <div class="flex gap-1">
        <Tooltip :text="__('Mark all as read')">
          <Button variant="ghost" @click="markAllAsRead">
            <template #icon>
              <MarkAsDoneIcon class="h-4 w-4" />
            </template>
          </Button>
        </Tooltip>
        
      </div>
    </div>

    <!-- List -->
    <div v-if="notifications.data?.length" class="divide-y divide-outline-gray-modals overflow-auto text-base">
      <RouterLink
        v-for="n in notifications.data"
        :key="n.name"
        :to="getRoute(n)"
        class="flex cursor-pointer items-start gap-2.5 px-4 py-2.5 hover:bg-surface-gray-2"
        @click="markAsRead(n.name || n.notification_type_doc)"
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

    <!-- Empty -->
    <div v-else class="flex flex-1 flex-col items-center justify-center gap-2">
      <NotificationsIcon class="h-20 w-20 text-ink-gray-2" />
      <div class="text-lg font-medium text-ink-gray-4">
        {{ __('No new notifications') }}
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

    <!-- Audio -->
    <audio ref="notificationSound" src="/notification.mp3" preload="auto" />
  </div>
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

onClickOutside(target, () => visible.value && toggle(), {
  ignore: ['#notifications-btn'],
})

const showPopup = ref(false)
const popupNotification = ref(null)
const notificationPermission = ref(Notification.permission)
const notificationSound = ref(null)

function requestNotificationPermission() {
  if (!("Notification" in window)) return
  Notification.requestPermission().then(permission => {
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
    notificationSound.value.play().catch(() => {})
  }
}

function showPushNotification(notification) {
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

// Fixed route for now
function getRoute(notification) {
  return {
    name: "Tasks"
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
