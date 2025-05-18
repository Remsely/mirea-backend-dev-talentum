import type { Employee } from './auth';
import type { Goal } from './goals';

export type FeedbackRequestStatus = 'pending' | 'completed';

export interface SelfAssessment {
  id: number;
  goal: number;
  rating: number;
  comments: string;
  areas_to_improve: string;
  created_dttm: string;
}

export interface FeedbackRequest {
  id: number;
  goal: number;
  reviewer: number;
  requested_by: number;
  message: string;
  status: FeedbackRequestStatus;
  created_dttm: string;
}

export interface FeedbackRequestDetail {
  id: number;
  goal: Goal;
  reviewer: Employee;
  requested_by: Employee;
  message: string;
  status: FeedbackRequestStatus;
  created_dttm: string;
}

export interface PeerFeedback {
  id: number;
  feedback_request: number;
  rating: number;
  comments: string;
  areas_to_improve: string;
  created_dttm: string;
}

export interface ExpertEvaluation {
  id: number;
  goal: number;
  expert: number;
  final_rating: number;
  comments: string;
  areas_to_improve: string;
  created_dttm: string;
}

export interface ExpertEvaluationDetail {
  id: number;
  goal: Goal;
  expert: Employee;
  final_rating: number;
  comments: string;
  areas_to_improve: string;
  created_dttm: string;
} 