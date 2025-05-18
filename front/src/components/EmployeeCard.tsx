import React from 'react';
import type { Employee } from '../types/auth';

interface EmployeeCardProps {
  employee: Employee;
}

export const EmployeeCard: React.FC<EmployeeCardProps> = ({ employee }) => {
  return (
    <div className="subordinate-card">
      <div className="subordinate-photo">
        {employee.profile_photo_url ? (
          <img 
            src={employee.profile_photo_url} 
            alt={`${employee.user.first_name} ${employee.user.last_name}`} 
          />
        ) : (
          <div className="photo-placeholder">
            {employee.user.first_name[0]}{employee.user.last_name[0]}
          </div>
        )}
      </div>
      <div className="subordinate-info">
        <div className="subordinate-name">
          {employee.user.first_name} {employee.user.last_name}
        </div>
        <div className="subordinate-position">{employee.position}</div>
      </div>
    </div>
  );
}; 