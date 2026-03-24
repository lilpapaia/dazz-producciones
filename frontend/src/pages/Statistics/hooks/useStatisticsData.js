import { useState, useEffect } from 'react';
import { getCompleteStatistics, getAvailableYears, getCompanies } from '../../../services/api';
import { ROLES } from '../../../constants/roles';

export function useStatisticsData(user) {
  const currentYear = new Date().getFullYear();

  const [year, setYear] = useState(currentYear);
  const [quarter, setQuarter] = useState('');
  const [geoFilter, setGeoFilter] = useState('');
  const [companyId, setCompanyId] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [availableYears, setAvailableYears] = useState([currentYear]);

  // Cargar anos disponibles
  useEffect(() => {
    const loadYears = async () => {
      try {
        const response = await getAvailableYears();
        if (response.data && response.data.length > 0) {
          setAvailableYears(response.data);
          if (!response.data.includes(currentYear)) {
            setYear(response.data[0]);
          }
        }
      } catch (error) {
        console.error('Error loading available years:', error);
      }
    };
    loadYears();
  }, []);

  // Cargar empresas (ADMIN: todas del sistema, BOSS: solo las suyas)
  useEffect(() => {
    if (user?.role === ROLES.ADMIN) {
      const loadCompanies = async () => {
        try {
          const response = await getCompanies();
          setCompanies(response.data);
        } catch (error) {
          console.error('Error loading companies:', error);
        }
      };
      loadCompanies();
    } else if (user?.role === ROLES.BOSS && user.companies?.length > 0) {
      setCompanies(user.companies);
    }
  }, [user]);

  // Cargar datos cuando cambia cualquier filtro
  useEffect(() => {
    const loadStatistics = async () => {
      setLoading(true);
      try {
        const quarterNum = quarter !== '' ? parseInt(quarter) : null;
        const geoFilterValue = geoFilter !== '' ? geoFilter : null;
        const response = await getCompleteStatistics(year, quarterNum, geoFilterValue, companyId);
        setData(response.data);
      } catch (error) {
        console.error('Error cargando estadisticas:', error);
      } finally {
        setLoading(false);
      }
    };
    loadStatistics();
  }, [year, quarter, geoFilter, companyId]);

  return {
    year, setYear,
    quarter, setQuarter,
    geoFilter, setGeoFilter,
    companyId, setCompanyId,
    companies,
    availableYears,
    loading,
    data,
  };
}
