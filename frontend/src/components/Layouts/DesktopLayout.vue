<template>
  <div class="flex h-screen w-screen">
    <!-- Sidebar -->
    <div class="h-full border-r bg-surface-menu-bar">
      <AppSidebar />
    </div>

    <!-- Main + Notifications -->
    <div class="flex flex-1 h-full overflow-hidden relative">
      <!-- Main Content -->
      <div
        class="flex flex-col h-full overflow-auto bg-surface-white transition-all duration-300 ease-in-out"
        :class="{ 'w-[calc(100%-350px)]': showNotifications, 'w-full': !showNotifications }"
      >
        <AppHeader />
        <slot />
      </div>

      <!-- Notification Panel -->
      <Transition name="slide">
        <div
          v-if="showNotifications"
          class="h-full w-[350px] border-l bg-white shadow-md relative z-10 flex flex-col"
        >
          <!-- Notification Content -->
          <Notifications class="flex-1" />
        </div>
      </Transition>

      <!-- Bottom Right Toggle Button (collapse or open) -->
      <div class="fixed bottom-4 right-5 z-50">
        <Button
          variant="solid"
          theme="gray"
          class="rounded-full p-3 shadow-md w-12 h-12 flex items-center justify-center"
          @click="showNotifications = !showNotifications"
        >
          <FeatherIcon
            :name="showNotifications ? 'chevron-right' : 'bell'"
            class="w-6 h-6"
          />
        </Button>
      </div>
    </div>
  </div>
</template>

<script setup>
import AppSidebar from '@/components/Layouts/AppSidebar.vue'
import AppHeader from '@/components/Layouts/AppHeader.vue'
import Notifications from '@/components/Notifications.vue'
import { FeatherIcon, Button } from 'frappe-ui'
import { ref } from 'vue'

const showNotifications = ref(true) // panel is open by default
</script>

<style scoped>
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
}
</style>

