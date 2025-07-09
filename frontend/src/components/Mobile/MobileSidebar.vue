<template>
  <TransitionRoot :show="sidebarOpened">
    <Dialog as="div" @close="sidebarOpened = false" class="fixed inset-0 z-40">
      <TransitionChild
        as="template"
        enter="transition ease-in-out duration-200 transform"
        enter-from="-translate-x-full"
        enter-to="translate-x-0"
        leave="transition ease-in-out duration-200 transform"
        leave-from="translate-x-0"
        leave-to="-translate-x-full"
      >
        <div
          class="relative z-10 flex h-full w-[260px] flex-col justify-between border-r bg-surface-menu-bar transition-all duration-300 ease-in-out"
        >
          <div>
            <UserDropdown class="p-2" :isCollapsed="!sidebarOpened" />
          </div>
          <div class="flex-1 overflow-y-auto">
            <div class="mb-3 flex flex-col">
              <SidebarLink
                id="notifications-btn"
                :label="__('Notifications')"
                :icon="NotificationsIcon"
                :to="{ name: 'Notifications' }"
                class="relative mx-2 my-0.5"
              >
                <template #right>
                  <Badge
                    v-if="unreadNotificationsCount"
                    :label="unreadNotificationsCount"
                    variant="subtle"
                  />
                </template>
              </SidebarLink>
            </div>
            <div v-for="view in allViews" :key="view.label">
              <Section
                :label="view.name"
                :hideLabel="view.hideLabel"
                :opened="view.opened"
              >
                <template #header="{ opened, hide, toggle }">
                  <div
                    v-if="!hide"
                    class="ml-2 mt-4 flex h-7 w-auto cursor-pointer gap-1.5 px-1 text-base font-medium text-ink-gray-5 opacity-100 transition-all duration-300 ease-in-out"
                    @click="toggle()"
                  >
                    <FeatherIcon
                      name="chevron-right"
                      class="h-4 text-ink-gray-9 transition-all duration-300 ease-in-out"
                      :class="{ 'rotate-90': opened }"
                    />
                    <span>{{ __(view.name) }}</span>
                  </div>
                </template>
                <nav class="flex flex-col">
                  <SidebarLink
                    v-for="link in view.views"
                    :icon="link.icon"
                    :label="__(link.label)"
                    :to="link.to"
                    class="mx-2 my-0.5"
                  />
                </nav>
              </Section>
            </div>
          </div>
        </div>
      </TransitionChild>
      <TransitionChild
        as="template"
        enter="transition-opacity ease-linear duration-200"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="transition-opacity ease-linear duration-200"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <DialogOverlay class="fixed inset-0 bg-gray-600 bg-opacity-50" />
      </TransitionChild>
    </Dialog>
  </TransitionRoot>


  <!-- In-app Popup -->
  <Transition name="fade">
    <div
      v-if="showPopup"
      class="fixed bottom-5 right-5 z-50 max-w-sm rounded-lg bg-white p-4 shadow-lg border border-gray-200"
    >
      <div class="flex items-start gap-3">
        <UserAvatar v-if="popupNotification" :user="popupNotification.from_user || ''" size="md" />
        <div>
          <div class="text-sm font-medium">{{ popupNotification?.from_user || 'Someone' }}</div>
          <div class="text-sm text-gray-700" v-html="popupNotification?.notification_text" />
        </div>
      </div>
    </div>
  </Transition>
  <!-- Audio element for notification sound -->
  <audio ref="notificationSound" src="/assets/crm/frontend/notification.mp3" preload="auto" />
</template>
<script setup>
import {
  TransitionRoot,
  TransitionChild,
  Dialog,
  DialogOverlay,
} from '@headlessui/vue'
import Section from '@/components/Section.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import PinIcon from '@/components/Icons/PinIcon.vue'
import UserDropdown from '@/components/UserDropdown.vue'
import LeadsIcon from '@/components/Icons/LeadsIcon.vue'
import DealsIcon from '@/components/Icons/DealsIcon.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import OrganizationsIcon from '@/components/Icons/OrganizationsIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import NotificationsIcon from '@/components/Icons/NotificationsIcon.vue'
import SidebarLink from '@/components/SidebarLink.vue'
import { viewsStore } from '@/stores/views'
import { unreadNotificationsCount, notifications } from '@/stores/notifications'
import { computed, h } from 'vue'
import {ref, onBeforeUnmount, onMounted } from 'vue'

import { mobileSidebarOpened as sidebarOpened } from '@/composables/settings'
import { globalStore } from '@/stores/global'

const { getPinnedViews, getPublicViews } = viewsStore()

const links = [
  {
    label: 'Leads',
    icon: LeadsIcon,
    to: 'Leads',
  },
  {
    label: 'Deals',
    icon: DealsIcon,
    to: 'Deals',
  },
  {
    label: 'Contacts',
    icon: ContactsIcon,
    to: 'Contacts',
  },
  {
    label: 'Organizations',
    icon: OrganizationsIcon,
    to: 'Organizations',
  },
  {
    label: 'Notes',
    icon: NoteIcon,
    to: 'Notes',
  },
  {
    label: 'Tasks',
    icon: TaskIcon,
    to: 'Tasks',
  },
  {
    label: 'Call Logs',
    icon: PhoneIcon,
    to: 'Call Logs',
  },
  {
    label: 'Email Templates',
    icon: Email2Icon,
    to: 'Email Templates',
  },
]

const allViews = computed(() => {
  let _views = [
    {
      name: 'All Views',
      hideLabel: true,
      opened: true,
      views: links,
    },
  ]
  if (getPublicViews().length) {
    _views.push({
      name: 'Public views',
      opened: true,
      views: parseView(getPublicViews()),
    })
  }

  if (getPinnedViews().length) {
    _views.push({
      name: 'Pinned views',
      opened: true,
      views: parseView(getPinnedViews()),
    })
  }
  return _views
})

function parseView(views) {
  return views.map((view) => {
    return {
      label: view.label,
      icon: getIcon(view.route_name, view.icon),
      to: {
        name: view.route_name,
        params: { viewType: view.type || 'list' },
        query: { view: view.name },
      },
    }
  })
}

function getIcon(routeName, icon) {
  if (icon) return h('div', { class: 'size-auto' }, icon)

  switch (routeName) {
    case 'Leads':
      return LeadsIcon
    case 'Deals':
      return DealsIcon
    case 'Contacts':
      return ContactsIcon
    case 'Organizations':
      return OrganizationsIcon
    case 'Notes':
      return NoteIcon
    case 'Call Logs':
      return PhoneIcon
    default:
      return PinIcon
  }
}

const { $socket } = globalStore()
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
onBeforeUnmount(() => {
  $socket.off('crm_notification')
})

onMounted(() => {
  console.log("crm_notification subscribed")
  $socket.on('crm_notification', (notification) => {
    setTimeout(()=>{
      console.log("crm_notification reload")
      notifications.reload()
    }, 1000);

    console.log("crm_notification showPushNotification")
    showPushNotification(notification)
  })
})
</script>
