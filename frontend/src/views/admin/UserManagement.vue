<template>
  <div class="user-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>用户管理</span>
          <el-button type="primary" :icon="Plus" @click="handleCreate">
            添加用户
          </el-button>
        </div>
      </template>
      
      <!-- Filters -->
      <div class="filters">
        <el-select
          v-model="filters.is_active"
          placeholder="账号状态"
          clearable
          @change="handleSearch"
        >
          <el-option label="全部" :value="undefined" />
          <el-option label="正常" :value="true" />
          <el-option label="禁用" :value="false" />
        </el-select>
        
        <el-button :icon="Refresh" @click="loadUsers">刷新</el-button>
      </div>
      
      <!-- User Table -->
      <el-table
        v-loading="loading"
        :data="users"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column prop="username" label="用户名" width="150" />
        
        <el-table-column prop="email" label="邮箱" min-width="200" />
        
        <el-table-column prop="full_name" label="姓名" width="150">
          <template #default="{ row }">
            {{ row.full_name || '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="角色" width="200">
          <template #default="{ row }">
            <el-tag
              v-for="role in row.roles"
              :key="role"
              :type="role === 'admin' ? 'danger' : 'primary'"
              size="small"
              style="margin-right: 4px;"
            >
              {{ role === 'admin' ? '管理员' : '用户' }}
            </el-tag>
            <el-tag v-if="row.is_superuser" type="warning" size="small">
              超管
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '正常' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="注册时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '-' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              size="small"
              @click="handleEdit(row)"
            >
              编辑
            </el-button>
            <el-button
              type="danger"
              link
              size="small"
              :disabled="row.id === currentUser?.id"
              @click="handleDelete(row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- Pagination -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="loadUsers"
          @current-change="loadUsers"
        />
      </div>
    </el-card>
    
    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '添加用户'"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="用户名" prop="username" v-if="!isEdit">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        
        <el-form-item label="用户名" v-if="isEdit">
          <el-input :model-value="editingUser?.username" disabled />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="form.full_name" placeholder="请输入姓名" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        
        <el-form-item label="角色" prop="role_ids">
          <el-select
            v-model="form.role_ids"
            multiple
            placeholder="请选择角色"
            style="width: 100%"
          >
            <el-option
              v-for="role in roles"
              :key="role.id"
              :label="role.name === 'admin' ? '管理员' : '用户'"
              :value="role.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="超级管理员" v-if="currentUser?.is_superuser">
          <el-switch v-model="form.is_superuser" :disabled="editingUser?.id === currentUser?.id" />
        </el-form-item>
        
        <el-form-item label="账号状态">
          <el-switch
            v-model="form.is_active"
            active-text="正常"
            inactive-text="禁用"
            :disabled="editingUser?.id === currentUser?.id"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { FormInstance, FormRules, ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { userApi, UserListItem, Role } from '@/api/auth'
import { useUserStore } from '@/store'
import dayjs from 'dayjs'

const userStore = useUserStore()
const currentUser = computed(() => userStore.userInfo)

const loading = ref(false)
const users = ref<UserListItem[]>([])
const roles = ref<Role[]>([])

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
  pages: 0,
})

const filters = reactive({
  is_active: undefined as boolean | undefined,
})

const dialogVisible = ref(false)
const isEdit = ref(false)
const editingUser = ref<UserListItem | null>(null)
const submitLoading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  email: '',
  full_name: '',
  password: '',
  role_ids: [] as number[],
  is_active: true,
  is_superuser: false,
})

const formRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为3-50个字符', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 100, message: '密码长度为6-100个字符', trigger: 'blur' },
  ],
}

const formatDate = (date: string) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await userApi.listUsers({
      page: pagination.page,
      page_size: pagination.page_size,
      is_active: filters.is_active,
    })
    
    users.value = response.data.items
    pagination.total = response.data.total
    pagination.pages = response.data.pages
  } catch (error) {
    console.error('Failed to load users:', error)
  } finally {
    loading.value = false
  }
}

const loadRoles = async () => {
  try {
    const response = await userApi.listRoles()
    roles.value = response.data
  } catch (error) {
    console.error('Failed to load roles:', error)
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadUsers()
}

const resetForm = () => {
  form.username = ''
  form.email = ''
  form.full_name = ''
  form.password = ''
  form.role_ids = []
  form.is_active = true
  form.is_superuser = false
}

const handleCreate = () => {
  isEdit.value = false
  editingUser.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (user: UserListItem) => {
  isEdit.value = true
  editingUser.value = user
  
  form.email = user.email
  form.full_name = user.full_name || ''
  form.is_active = user.is_active
  form.is_superuser = user.is_superuser
  
  // Map role names to role IDs
  form.role_ids = roles.value
    .filter(r => user.roles.includes(r.name))
    .map(r => r.id)
  
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitLoading.value = true
    try {
      if (isEdit.value && editingUser.value) {
        // Update user
        await userApi.updateUser(editingUser.value.id, {
          email: form.email,
          full_name: form.full_name || undefined,
          is_active: form.is_active,
          is_superuser: form.is_superuser,
          role_ids: form.role_ids,
        })
        ElMessage.success('用户更新成功')
      } else {
        // Create user
        const roleNames = roles.value
          .filter(r => form.role_ids.includes(r.id))
          .map(r => r.name)
        
        await userApi.createUser(
          {
            username: form.username,
            email: form.email,
            password: form.password,
            full_name: form.full_name || undefined,
          },
          roleNames.length > 0 ? roleNames : ['user']
        )
        ElMessage.success('用户创建成功')
      }
      
      dialogVisible.value = false
      loadUsers()
    } catch (error) {
      console.error('Submit error:', error)
    } finally {
      submitLoading.value = false
    }
  })
}

const handleDelete = async (user: UserListItem) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    await userApi.deleteUser(user.id)
    ElMessage.success('用户删除成功')
    loadUsers()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('Delete error:', error)
    }
  }
}

onMounted(() => {
  loadUsers()
  loadRoles()
})
</script>

<style lang="scss" scoped>
.user-management {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .filters {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
  }
  
  .pagination {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>
