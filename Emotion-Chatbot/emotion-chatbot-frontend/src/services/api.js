import axios from 'axios';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: {
    'Content-Type': 'application/json'
  },
  timeout: 15000
});

export async function sendMessage(message, user_id = 'user1') {
  const { data } = await api.post('/chat', { message, user_id });
  return data;
}

export default api;
