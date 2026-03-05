import { useState, useEffect } from 'react';
import { getUsers, registerUser, deleteUser } from '../services/api';
import { Plus, Trash2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Users = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newUser, setNewUser] = useState({
    name: '',
    email: '',
    password: 'temporal123',
    role: 'user'
  });
  const { user: currentUser } = useAuth();

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      const response = await getUsers();
      setUsers(response.data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await registerUser(newUser);
      
      // PRIMERO: Cerrar modal y limpiar form
      setShowCreate(false);
      const tempPassword = newUser.password;
      const tempEmail = newUser.email;
      setNewUser({ name: '', email: '', password: 'temporal123', role: 'user' });
      
      // SEGUNDO: Recargar lista de usuarios
      await loadUsers();
      
      // TERCERO: Mostrar confirmación (después de recargar)
      alert(`✓ Usuario creado\n✓ Email: ${tempEmail}\n✓ Contraseña temporal: ${tempPassword}`);
      
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Error al crear usuario: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDelete = async (userId) => {
    if (!confirm('¿Eliminar este usuario?')) return;
    
    try {
      await deleteUser(userId);
      await loadUsers(); // Recargar lista
      alert('✓ Usuario eliminado correctamente');
    } catch (error) {
      console.error('Error deleting user:', error);
      alert('Error al eliminar usuario: ' + (error.response?.data?.detail || error.message));
    }
  };

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
        <div className="flex items-center justify-between mb-8">
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
                    onChange={(e) => setNewUser({...newUser, name: e.target.value})}
                    className="w-full bg-zinc-950 border border-zinc-700 rounded-sm px-4 py-2.5 text-zinc-100 focus:outline-none focus:border-amber-500"
                    placeholder="Julieta García"
                  />
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
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-zinc-400 mb-2 tracking-wider">ROL</label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setNewUser({...newUser, role: 'user'})}
                    className={`p-4 rounded-sm border-2 transition-all ${
                      newUser.role === 'user'
                        ? 'border-amber-500 bg-amber-500/10'
                        : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                    }`}
                  >
                    <div className="text-3xl mb-2">👤</div>
                    <p className="font-semibold">Usuario</p>
                    <p className="text-xs text-zinc-500 mt-1">Solo ve sus proyectos</p>
                  </button>

                  <button
                    onClick={() => setNewUser({...newUser, role: 'admin'})}
                    className={`p-4 rounded-sm border-2 transition-all ${
                      newUser.role === 'admin'
                        ? 'border-amber-500 bg-amber-500/10'
                        : 'border-zinc-700 bg-zinc-900 hover:border-zinc-600'
                    }`}
                  >
                    <div className="text-3xl mb-2">👑</div>
                    <p className="font-semibold">Admin</p>
                    <p className="text-xs text-zinc-500 mt-1">Acceso completo</p>
                  </button>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => setShowCreate(false)}
                  className="flex-1 px-6 py-2.5 bg-zinc-800 hover:bg-zinc-700 text-zinc-100 rounded-sm transition-colors font-semibold"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleCreate}
                  className="flex-1 px-6 py-2.5 bg-amber-500 hover:bg-amber-600 text-zinc-950 font-bold rounded-sm transition-all shadow-lg shadow-amber-500/30"
                >
                  Crear Usuario
                </button>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {users.map((user) => (
            <div
              key={user.id}
              className="bg-zinc-900 border border-zinc-800 rounded-sm p-5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-zinc-800 flex items-center justify-center text-xl">
                    {user.role === 'admin' ? '👑' : '👤'}
                  </div>
                  <div>
                    <div className="flex items-center gap-3">
                      <h3 className="font-semibold text-zinc-100">{user.name}</h3>
                      <span className={`px-3 py-1 text-xs font-mono tracking-wider rounded-sm ${
                        user.role === 'admin'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-zinc-700/50 text-zinc-400 border border-zinc-600'
                      }`}>
                        {user.role === 'admin' ? 'ADMIN' : 'USUARIO'}
                      </span>
                    </div>
                    <p className="text-sm text-zinc-500 font-mono mt-1">{user.email}</p>
                  </div>
                </div>
                
                {user.id !== currentUser?.id && (
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDelete(user.id)}
                      className="px-4 py-2 bg-red-900/20 hover:bg-red-900/30 text-red-400 hover:text-red-300 rounded-sm transition-colors text-sm border border-red-900/30"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Users;
