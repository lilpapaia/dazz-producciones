import { useState, useEffect } from 'react';
import { getUsers, registerUser, deleteUser, updateUser, getCompanies } from '../services/api';
import { Plus, Trash2, Edit, Building2 } from 'lucide-react';
import { showSuccess, showError } from '../utils/toast';
import { ROLES } from '../constants/roles';
import { useAuth } from '../context/AuthContext';
import useEscapeKey from '../hooks/useEscapeKey';
import CompanyMultiSelect from '../components/CompanyMultiSelect';
import StatusBadge from '../components/common/StatusBadge';
import ConfirmDialog from '../components/ConfirmDialog';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [showCreate, setShowCreate] = useState(false);
  const [showEdit, setShowEdit] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editInitial, setEditInitial] = useState(null);
  const [deleteUserId, setDeleteUserId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    username: '',
    role: ROLES.WORKER,
    company_ids: []
  });
  const { user: currentUser } = useAuth();

  useEscapeKey(() => setShowCreate(false), showCreate);
  useEscapeKey(() => { setShowEdit(false); setEditingUser(null); }, showEdit);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoadError(false);
      const [usersRes, companiesRes] = await Promise.all([
        getUsers(),
        getCompanies()
      ]);
      setUsers(usersRes.data);
      setCompanies(companiesRes.data);
    } catch {
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    setSubmitting(true);
    try {
      await registerUser(newUser);
      
      // PRIMERO: Cerrar modal y limpiar form
      setShowCreate(false);
      const tempEmail = newUser.email;
      setNewUser({
        name: '',
        email: '',
        username: '',
            role: ROLES.WORKER,
        company_ids: []
      });
      
      // SEGUNDO: Recargar lista de usuarios
      await loadData();
      
      // TERCERO: Mostrar confirmación (después de recargar)
      showSuccess(`Usuario creado. Email enviado a ${tempEmail} para configurar contraseña`);
      
    } catch (error) {
      console.error('Error creating user:', error);
      const detail = error.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map(d => d.msg || d).join(', ') : (typeof detail === 'string' ? detail : error.message);
      showError('Error al crear usuario: ' + msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleEdit = async () => {
    setSubmitting(true);
    try {
      const payload = { ...editingUser };
      if (!payload.password || !payload.password.trim()) delete payload.password;
      await updateUser(payload.id, payload);
      
      // Cerrar modal
      setShowEdit(false);
      setEditingUser(null);
      
      // Recargar lista
      await loadData();
      
      showSuccess('Usuario actualizado correctamente');
      
    } catch (error) {
      console.error('Error updating user:', error);
      const detail = error.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map(d => d.msg || d).join(', ') : (typeof detail === 'string' ? detail : error.message);
      showError('Error al actualizar usuario: ' + msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (userId) => {
    setDeleteUserId(null);
    setSubmitting(true);
    try {
      await deleteUser(userId);
      await loadData();
      showSuccess('Usuario eliminado correctamente');
    } catch (error) {
      console.error('Error deleting user:', error);
      const detail = error.response?.data?.detail;
      const msg = Array.isArray(detail) ? detail.map(d => d.msg || d).join(', ') : (typeof detail === 'string' ? detail : error.message);
      showError('Error al eliminar usuario: ' + msg);
    } finally {
      setSubmitting(false);
    }
  };

  const openEditModal = (user) => {
    const values = {
      id: user.id,
      name: user.name,
      email: user.email,
      username: user.username || '',
      password: '',
      role: user.role,
      company_ids: user.companies?.map(c => c.id) || []
    };
    setEditingUser(values);
    setEditInitial({ ...values, company_ids: [...values.company_ids] });
    setShowEdit(true);
  };

  const editHasChanges = () => {
    if (!editingUser || !editInitial) return false;
    if (editingUser.name !== editInitial.name) return true;
    if (editingUser.email !== editInitial.email) return true;
    if (editingUser.username !== editInitial.username) return true;
    if (editingUser.role !== editInitial.role) return true;
    if (editingUser.password && editingUser.password.trim()) return true;
    const a = [...editingUser.company_ids].sort();
    const b = [...editInitial.company_ids].sort();
    if (a.length !== b.length || a.some((v, i) => v !== b[i])) return true;
    return false;
  };

  // Generar username automático del nombre
  const generateUsername = (name) => {
    if (!name) return '';
    return name
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '') // Quitar acentos
      .replace(/[^a-z0-9]/g, '') // Solo letras y números
      .slice(0, 15); // Max 15 chars
  };

  const handleNameChange = (name, isEdit = false) => {
    const autoUsername = generateUsername(name);
    
    if (isEdit) {
      setEditingUser({
        ...editingUser, 
        name,
        username: editingUser.username || autoUsername
      });
    } else {
      setNewUser({
        ...newUser, 
        name,
        username: newUser.username || autoUsername
      });
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        {loadError && (
          <div className="bg-red-400/[.06] text-red-400 border border-red-400/[.12] rounded p-2.5 text-[12px] flex items-center gap-2 mb-4">
            Error al cargar usuarios
            <button onClick={loadData} className="text-amber-500 hover:text-amber-400 ml-1 font-semibold">Reintentar</button>
          </div>
        )}
        {/* MÓVIL: Header centrado */}
        <div className="flex flex-col items-center text-center gap-4 mb-8 md:hidden">
          <h2 className="text-4xl font-bebas tracking-wider">GESTIÓN DE USUARIOS</h2>
          <p className="text-zinc-500 font-mono text-sm">Administrar accesos al sistema</p>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 font-bebas text-lg tracking-wider flex items-center gap-2"
          >
            <Plus size={20} /> NUEVO USUARIO
          </button>
        </div>

        {/* DESKTOP: Header horizontal */}
        <div className="hidden md:flex items-center justify-between mb-8">
          <div>
            <h2 className="text-4xl font-bebas tracking-wider mb-2">GESTIÓN DE USUARIOS</h2>
            <p className="text-zinc-500 font-mono text-sm">Administrar accesos al sistema</p>
          </div>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="px-6 py-3 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 font-bebas text-lg tracking-wider flex items-center gap-2"
          >
            <Plus size={20} /> NUEVO USUARIO
          </button>
        </div>

        {/* MODAL CREAR USUARIO */}
        {showCreate && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 mb-6">
            <h3 className="text-xl font-bebas tracking-wider mb-4">CREAR NUEVO USUARIO</h3>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOMBRE COMPLETO</label>
                  <input
                    type="text"
                    value={newUser.name}
                    onChange={(e) => handleNameChange(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                    placeholder="Julieta García"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">USERNAME</label>
                  <input
                    type="text"
                    value={newUser.username}
                    onChange={(e) => setNewUser({...newUser, username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '')})}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                    placeholder="julietagarcia"
                  />
                  <p className="text-xs text-zinc-500 mt-1">Para iniciar sesión (solo letras, números y _)</p>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL</label>
                <input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({...newUser, email: e.target.value})}
                  className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                  placeholder="usuario@dazzle-agency.com"
                />
                <p className="text-xs text-zinc-500 mt-1">Recibirá email para configurar contraseña</p>
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ROL</label>
                <div className="grid grid-cols-3 gap-4">
                  <button
                    onClick={() => setNewUser({...newUser, role: ROLES.ADMIN})}
                    className={`p-4 rounded-sm border-2 transition-all ${
                      newUser.role === ROLES.ADMIN
                        ? 'border-amber-500 bg-amber-500/10'
                        : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                    }`}
                    type="button"
                  >
                    <div className="text-3xl mb-2">👑</div>
                    <p className="font-semibold">Admin</p>
                    <p className="text-xs text-zinc-500 mt-1">Acceso total</p>
                  </button>

                  <button
                    onClick={() => setNewUser({...newUser, role: ROLES.BOSS})}
                    className={`p-4 rounded-sm border-2 transition-all ${
                      newUser.role === ROLES.BOSS
                        ? 'border-amber-500 bg-amber-500/10'
                        : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                    }`}
                    type="button"
                  >
                    <div className="text-3xl mb-2">🎯</div>
                    <p className="font-semibold">Boss</p>
                    <p className="text-xs text-zinc-500 mt-1">Gestiona empresa</p>
                  </button>

                  <button
                    onClick={() => setNewUser({...newUser, role: ROLES.WORKER})}
                    className={`p-4 rounded-sm border-2 transition-all ${
                      newUser.role === ROLES.WORKER
                        ? 'border-amber-500 bg-amber-500/10'
                        : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                    }`}
                    type="button"
                  >
                    <div className="text-3xl mb-2">👤</div>
                    <p className="font-semibold">Worker</p>
                    <p className="text-xs text-zinc-500 mt-1">Sus proyectos</p>
                  </button>
                </div>
              </div>

              {/* Selector de empresas (BOSS/WORKER) o texto informativo (ADMIN) */}
              {newUser.role === 'ADMIN' ? (
                <div className="flex items-center gap-2 py-2">
                  <Building2 size={14} className="text-zinc-500" />
                  <span className="text-xs text-zinc-500">Acceso a todas las empresas</span>
                </div>
              ) : (
                <CompanyMultiSelect
                  selectedCompanyIds={newUser.company_ids}
                  onChange={(ids) => setNewUser({...newUser, company_ids: ids})}
                  companies={companies}
                  label="Empresas asignadas"
                />
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowCreate(false)}
                  className="flex-1 px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
                  type="button"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreate}
                  disabled={!newUser.name || !newUser.email || !newUser.username || (newUser.role !== 'ADMIN' && newUser.company_ids.length === 0) || submitting}
                  className="flex-1 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                  type="button"
                >
                  {submitting ? 'Guardando...' : 'Crear Usuario'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* MODAL EDITAR USUARIO */}
        {showEdit && editingUser && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-zinc-900 border border-zinc-800 rounded-sm p-6 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
              <h3 className="text-xl font-bebas tracking-wider mb-4">EDITAR USUARIO</h3>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NOMBRE COMPLETO</label>
                    <input
                      type="text"
                      value={editingUser.name}
                      onChange={(e) => handleNameChange(e.target.value, true)}
                      className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">USERNAME</label>
                    <input
                      type="text"
                      value={editingUser.username}
                      onChange={(e) => setEditingUser({...editingUser, username: e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, '')})}
                      className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">EMAIL</label>
                  <input
                    type="email"
                    value={editingUser.email}
                    onChange={(e) => setEditingUser({...editingUser, email: e.target.value})}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">NUEVA CONTRASEÑA (opcional)</label>
                  <input
                    type="password"
                    value={editingUser.password}
                    onChange={(e) => setEditingUser({...editingUser, password: e.target.value})}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                    placeholder="Dejar vacío para no cambiar"
                    autoComplete="new-password"
                    name="new-password"
                  />
                </div>

                <div>
                  <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ROL</label>
                  <div className="grid grid-cols-3 gap-4">
                    <button
                      onClick={() => setEditingUser({...editingUser, role: ROLES.ADMIN})}
                      className={`p-4 rounded-sm border-2 transition-all ${
                        editingUser.role === ROLES.ADMIN
                          ? 'border-amber-500 bg-amber-500/10'
                          : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                      }`}
                      type="button"
                    >
                      <div className="text-3xl mb-2">👑</div>
                      <p className="font-semibold">Admin</p>
                    </button>

                    <button
                      onClick={() => setEditingUser({...editingUser, role: ROLES.BOSS})}
                      className={`p-4 rounded-sm border-2 transition-all ${
                        editingUser.role === ROLES.BOSS
                          ? 'border-amber-500 bg-amber-500/10'
                          : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                      }`}
                      type="button"
                    >
                      <div className="text-3xl mb-2">🎯</div>
                      <p className="font-semibold">Boss</p>
                    </button>

                    <button
                      onClick={() => setEditingUser({...editingUser, role: ROLES.WORKER})}
                      className={`p-4 rounded-sm border-2 transition-all ${
                        editingUser.role === ROLES.WORKER
                          ? 'border-amber-500 bg-amber-500/10'
                          : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                      }`}
                      type="button"
                    >
                      <div className="text-3xl mb-2">👤</div>
                      <p className="font-semibold">Worker</p>
                    </button>
                  </div>
                </div>

                {editingUser.role === 'ADMIN' ? (
                  <div className="flex items-center gap-2 py-2">
                    <Building2 size={14} className="text-zinc-500" />
                    <span className="text-xs text-zinc-500">Acceso a todas las empresas</span>
                  </div>
                ) : (
                  <CompanyMultiSelect
                    selectedCompanyIds={editingUser.company_ids}
                    onChange={(ids) => setEditingUser({...editingUser, company_ids: ids})}
                    companies={companies}
                    label="Empresas asignadas"
                  />
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    onClick={() => {
                      setShowEdit(false);
                      setEditingUser(null);
                    }}
                    className="flex-1 px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
                    type="button"
                  >
                    Cancelar
                  </button>
                  <button
                    onClick={handleEdit}
                    disabled={!editingUser.name || !editingUser.email || !editingUser.username || !editHasChanges() || submitting}
                    className="flex-1 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
                    type="button"
                  >
                    {submitting ? 'Guardando...' : 'Guardar Cambios'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* LISTA DE USUARIOS */}
        <div className="space-y-3">
          {users.map((user) => (
            <div
              key={user.id}
              className="bg-zinc-900 border border-zinc-800 rounded-sm p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* Nombre arriba */}
                  <h3 className="text-lg font-semibold text-zinc-100 mb-2">{user.name}</h3>
                  
                  {/* Username + Badge en misma línea */}
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    {user.username && (
                      <>
                        <span className="text-zinc-500 font-mono text-sm">@{user.username}</span>
                        <span className="text-zinc-600">•</span>
                      </>
                    )}
                    <StatusBadge type="role" value={user.role} />
                  </div>
                  
                  {/* Email */}
                  <p className="text-sm text-zinc-500 font-mono mb-2">{user.email}</p>
                  
                  {/* NUEVO: Empresas */}
                  {user.companies && user.companies.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                      {user.companies.map(company => (
                        <span
                          key={company.id}
                          className="px-2 py-1 bg-zinc-800 border border-zinc-700 text-zinc-300 text-xs rounded-sm"
                        >
                          🏢 {company.name}
                        </span>
                      ))}
                    </div>
                  )}
                  {user.role !== 'ADMIN' && (!user.companies || user.companies.length === 0) && (
                    <p className="text-xs text-amber-500 mt-2">⚠️ Sin empresas asignadas</p>
                  )}
                </div>
                
                {/* Botones a la derecha */}
                {user.id !== currentUser?.id && (
                  <div className="flex gap-2 flex-shrink-0">
                    <button
                      onClick={() => openEditModal(user)}
                      className="p-2 bg-blue-900/20 hover:bg-blue-900/30 text-blue-400 hover:text-blue-300 rounded-sm transition-colors border border-blue-900/30"
                    >
                      <Edit className="w-5 h-5" />
                    </button>
                    <button
                      onClick={() => setDeleteUserId(user.id)}
                      disabled={submitting}
                      className={`p-2 bg-red-900/20 hover:bg-red-900/30 text-red-400 hover:text-red-300 rounded-sm transition-colors border border-red-900/30 ${submitting ? 'opacity-50 cursor-not-allowed' : ''}`}
                    >
                      <Trash2 className="w-5 h-5" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>

      <ConfirmDialog
        isOpen={!!deleteUserId}
        onClose={() => setDeleteUserId(null)}
        onConfirm={() => handleDelete(deleteUserId)}
        title="¿Eliminar usuario?"
        message="Esta acción eliminará al usuario de forma permanente. No se puede deshacer."
        confirmText="Eliminar"
        cancelText="Cancelar"
        type="danger"
      />
    </div>
  );
};

export default Users;
