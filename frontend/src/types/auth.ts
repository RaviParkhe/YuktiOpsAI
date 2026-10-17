export type UserRole = 'ADMIN' | 'DEVELOPER'

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  avatar: string
  handle: string
  title: string
  isOnline: boolean
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
}
