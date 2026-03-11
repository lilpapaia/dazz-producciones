import { useState, useCallback } from 'react';

export function useExpandedState() {
  const [expandedProjects, setExpandedProjects] = useState(new Set());
  const [expandedCompanies, setExpandedCompanies] = useState(new Set());

  const toggleProject = useCallback((projectId) => {
    setExpandedProjects(prev => {
      const next = new Set(prev);
      next.has(projectId) ? next.delete(projectId) : next.add(projectId);
      return next;
    });
  }, []);

  const toggleCompany = useCallback((id) => {
    setExpandedCompanies(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }, []);

  return { expandedProjects, expandedCompanies, toggleProject, toggleCompany };
}
