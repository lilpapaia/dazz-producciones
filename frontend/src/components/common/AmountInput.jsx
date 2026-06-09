import { useState, useEffect, useRef } from 'react';

/**
 * Input de importes robusto frente a locales (coma vs punto como separador decimal).
 *
 * Problema que resuelve:
 * <input type="number"> devuelve "" en estados intermedios (ej. al teclear la coma en
 * "1500,") y el separador decimal aceptado depende del SO/navegador/locale. Combinado
 * con `parseFloat(...) || 0` + recálculo en vivo sobre un input controlado, el importe
 * "salta" a 0 mientras se escribe y se pierde lo tecleado.
 *
 * Solución (plan B+D):
 *  - type="text" + inputMode="decimal" → el separador lo controlamos nosotros, no el SO.
 *  - Mantiene el texto crudo mientras se edita (no se clobberea con re-renders).
 *  - Acepta coma O punto, normaliza coma→punto antes de parsear.
 *  - Solo entrega el número parseado en `onCommit` al perder foco / pulsar Enter (D),
 *    evitando recálculos en cada keystroke.
 *
 * @param {number|string|null} value  Valor canónico (número). Se muestra cuando no se edita.
 * @param {(n:number|null)=>void} onCommit  Llamado en blur/Enter con el valor parseado.
 * @param {number} [decimals=2]  Decimales a los que se redondea en commit (0 para %).
 * @param {number} [min]  Clamp inferior aplicado en commit.
 * @param {number} [max]  Clamp superior aplicado en commit.
 * @param {boolean} [allowEmpty=false]  Si true, vacío → onCommit(null) y muestra "".
 */
const AmountInput = ({
  value,
  onCommit,
  decimals = 2,
  min,
  max,
  allowEmpty = false,
  disabled = false,
  className = '',
  placeholder = '',
  ...rest
}) => {
  const [raw, setRaw] = useState('');
  const editing = useRef(false);

  // Formatea el número canónico a texto para mostrar cuando NO se está editando
  const formatValue = (v) => {
    if (v == null || v === '') return '';
    const n = Number(v);
    if (Number.isNaN(n)) return '';
    return String(n);
  };

  // Sincroniza el texto mostrado con el prop cuando cambia desde fuera (carga IA,
  // navegación entre tickets, recálculo por otro campo...). Nunca pisa lo que el
  // usuario está escribiendo (editing.current).
  useEffect(() => {
    if (!editing.current) {
      setRaw(formatValue(value));
    }
  }, [value]);

  const handleFocus = () => {
    editing.current = true;
  };

  const handleChange = (e) => {
    editing.current = true;
    const input = e.target.value;
    // Acepta solo: signo opcional + dígitos + un único separador (coma o punto) + dígitos.
    // Rechaza el resto manteniendo el texto previo (no clobberea).
    if (input === '' || /^-?\d*[.,]?\d*$/.test(input)) {
      setRaw(input);
    }
  };

  const commit = () => {
    editing.current = false;
    const normalized = raw.replace(',', '.');

    if (allowEmpty && normalized.trim() === '') {
      setRaw('');
      onCommit(null);
      return;
    }

    let n = parseFloat(normalized);
    if (Number.isNaN(n)) n = 0;
    if (typeof min === 'number') n = Math.max(min, n);
    if (typeof max === 'number') n = Math.min(max, n);
    if (decimals != null) {
      const f = Math.pow(10, decimals);
      n = Math.round(n * f) / f;
    }
    setRaw(formatValue(n));
    onCommit(n);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      e.currentTarget.blur();
    }
  };

  return (
    <input
      type="text"
      inputMode="decimal"
      value={raw}
      onFocus={handleFocus}
      onChange={handleChange}
      onBlur={commit}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      placeholder={placeholder}
      className={className}
      {...rest}
    />
  );
};

export default AmountInput;
