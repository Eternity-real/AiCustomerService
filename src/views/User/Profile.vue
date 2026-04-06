<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useAuthStore } from '../../stores/auth'
import { ElMessage, FormRules } from 'element-plus'

const authStore = useAuthStore()
const user = computed(() => authStore.currentUser)
const userInitial = computed(() => user.value?.nickname?.charAt(0).toUpperCase() || 'U')

const loading = ref(false)
// 👇 修改这里：移除泛型，使用 any 类型
const profileFormRef = ref(null) as any

const profileForm = reactive({
  nickname: '',
})

const profileRules: FormRules = {
  nickname: [{ required: true, message: '请输入昵称', trigger: 'blur' }],
}

const updateProfile = async () => {
  if (!profileFormRef.value) return

  await profileFormRef.value.validate(async (valid: boolean) => {
    if (valid) {
      loading.value = true
      try {
        await authStore.updateProfile(profileForm.nickname)
        ElMessage.success('修改成功')
      } catch (error) {
        ElMessage.error('修改失败')
      } finally {
        loading.value = false
      }
    }
  })
}

const formatDateTime = (dateStr: string) => {
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => {
  if (user.value) {
    profileForm.nickname = user.value.nickname
  }
})
</script>
