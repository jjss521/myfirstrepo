import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

export const health = () => api.get('/health')
export const getProjectTypes = () => api.get('/project-types')
export const getSections = () => api.get('/sections')
export const generateDoc = (data) => api.post('/generate', data)
export const uploadDoc = (formData) => api.post('/upload', formData)

export default api
