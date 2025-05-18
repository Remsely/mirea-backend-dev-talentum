import type { 
  SelfAssessment, 
  FeedbackRequest, 
  FeedbackRequestDetail,
  PeerFeedback,
  ExpertEvaluation 
} from '../types/feedback';
import axiosInstance from './axios';

export const feedbackApi = {
  // Self Assessment
  addSelfAssessment: async (goalId: number, data: Partial<SelfAssessment>): Promise<SelfAssessment> => {
    const response = await axiosInstance.post<SelfAssessment>(`/feedback/goals/${goalId}/self-assessment/`, data);
    return response.data;
  },

  getSelfAssessment: async (goalId: number): Promise<SelfAssessment> => {
    const response = await axiosInstance.get<SelfAssessment>(`/feedback/goals/${goalId}/self-assessment/`);
    return response.data;
  },

  // Feedback Requests
  createFeedbackRequest: async (data: Partial<FeedbackRequest>): Promise<FeedbackRequest> => {
    const response = await axiosInstance.post<FeedbackRequest>('/feedback/requests/', data);
    return response.data;
  },

  getMyFeedbackRequests: async (): Promise<FeedbackRequestDetail[]> => {
    const response = await axiosInstance.get<FeedbackRequestDetail[]>('/feedback/requests/my-requests/');
    return response.data;
  },

  getPendingFeedbackRequests: async (): Promise<FeedbackRequestDetail[]> => {
    const response = await axiosInstance.get<FeedbackRequestDetail[]>('/feedback/requests/pending/');
    return response.data;
  },

  // Peer Feedback
  submitPeerFeedback: async (requestId: number, data: Partial<PeerFeedback>): Promise<PeerFeedback> => {
    const response = await axiosInstance.post<PeerFeedback>(`/feedback/requests/${requestId}/feedback/`, data);
    return response.data;
  },

  getPeerFeedbacks: async (goalId: number): Promise<PeerFeedback[]> => {
    const response = await axiosInstance.get<PeerFeedback[]>(`/feedback/goals/${goalId}/peer-feedbacks/`);
    return response.data;
  },

  // Expert Evaluation
  submitExpertEvaluation: async (goalId: number, data: Partial<ExpertEvaluation>): Promise<ExpertEvaluation> => {
    const response = await axiosInstance.post<ExpertEvaluation>(`/feedback/goals/${goalId}/expert-evaluation/`, data);
    return response.data;
  },

  getExpertEvaluation: async (goalId: number): Promise<ExpertEvaluation> => {
    const response = await axiosInstance.get<ExpertEvaluation>(`/feedback/goals/${goalId}/expert-evaluation/`);
    return response.data;
  },

  // For expertise leaders
  getGoalsPendingExpertEvaluation: async (): Promise<number[]> => {
    const response = await axiosInstance.get<number[]>('/feedback/goals/pending-expert-evaluation/');
    return response.data;
  },
}; 