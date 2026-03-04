import { z } from 'zod'

// simple zod schema for email/password
export const authSchema = z.object({
  email: z
    .string()
    .min(1, { message: 'Email is required' })
    .email({ message: 'Please enter a valid email' }),
  password: z
    .string()
    .min(6, { message: 'Password must be at least 6 characters' }),
})

export function validateAuthInput(data) {
  const result = authSchema.safeParse(data)
  if (result.success) return { success: true, data: result.data }
  const errors = Object.values(result.error.flatten().fieldErrors)
    .flat()
    .filter(Boolean)
  return { success: false, errors }
}
