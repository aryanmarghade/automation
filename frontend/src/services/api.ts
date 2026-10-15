import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: Record<string, any>;
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
}

export interface WorkflowItem {
  id: string;
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  is_active: boolean;
  tags?: string[];
  created_at: string;
  updated_at: string;
}

export interface ToolDef {
  id: string;
  name: string;
  description: string;
  category: string;
  risk_level: string;
  requires_confirmation: boolean;
  parameters: Array<{
    name: string;
    type: string;
    description: string;
    required: boolean;
    default?: any;
    options?: string[];
  }>;
}

export const WorkflowService = {
  list: async () => (await api.get<WorkflowItem[]>('/workflows')).data,
  get: async (id: string) => (await api.get<WorkflowItem>(`/workflows/${id}`)).data,
  create: async (data: Partial<WorkflowItem>) => (await api.post<WorkflowItem>('/workflows', data)).data,
  update: async (id: string, data: Partial<WorkflowItem>) => (await api.put<WorkflowItem>(`/workflows/${id}`, data)).data,
  delete: async (id: string) => (await api.delete(`/workflows/${id}`)).data,
  validate: async (data: { nodes: WorkflowNode[]; edges: WorkflowEdge[] }) => (await api.post('/workflows/validate', data)).data,
  run: async (id: string, inputs: Record<string, any> = {}) => (await api.post(`/workflows/${id}/run`, { inputs })).data,
};

export const ToolService = {
  list: async () => (await api.get<ToolDef[]>('/tools')).data,
  test: async (toolId: string, params: Record<string, any>) => (await api.post(`/tools/${toolId}/test`, params)).data,
};

export const AgentService = {
  plan: async (objective: string, attached_files: string[] = [], model_provider = 'ollama', model_name = 'llama3.2:latest') =>
    (await api.post('/agent/plan', { objective, attached_files, model_provider, model_name })).data,
  execute: async (objective: string, plan: any, autonomy_level = 'supervised', model_provider = 'ollama', model_name = 'llama3.2:latest') =>
    (await api.post('/agent/execute', { objective, plan, autonomy_level, model_provider, model_name })).data,
  pauseTask: async (taskId: string) => (await api.post(`/agent/tasks/${taskId}/pause`)).data,
  resumeTask: async (taskId: string) => (await api.post(`/agent/tasks/${taskId}/resume`)).data,
  cancelTask: async (taskId: string) => (await api.post(`/agent/tasks/${taskId}/cancel`)).data,
  convertToWorkflow: async (plan: any, workflowName?: string) =>
    (await api.post('/agent/plan/convert-to-workflow', { plan, workflow_name: workflowName })).data,
  listTasks: async () => (await api.get('/agent/tasks')).data,
};

export const FileService = {
  listFiles: async () => (await api.get('/workspace/files')).data,
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return (await api.post('/workspace/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data;
  },
};

export const ExecutionService = {
  list: async () => (await api.get('/executions')).data,
  get: async (id: string) => (await api.get(`/executions/${id}`)).data,
  retry: async (id: string) => (await api.post(`/executions/${id}/retry`)).data,
};

export const ScheduleService = {
  list: async () => (await api.get('/schedules')).data,
  create: async (data: any) => (await api.post('/schedules', data)).data,
  pause: async (id: string) => (await api.post(`/schedules/${id}/pause`)).data,
  resume: async (id: string) => (await api.post(`/schedules/${id}/resume`)).data,
  delete: async (id: string) => (await api.delete(`/schedules/${id}`)).data,
};

export const NotificationService = {
  list: async () => (await api.get('/notifications')).data,
  markRead: async (id: string) => (await api.post(`/notifications/${id}/read`)).data,
  clearAll: async () => (await api.delete('/notifications')).data,
};
