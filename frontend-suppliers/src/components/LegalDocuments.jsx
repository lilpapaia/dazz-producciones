import { useState, useRef, useEffect } from 'react';
import { X, Download } from 'lucide-react';
import useEscapeKey from '../hooks/useEscapeKey';

// ============================================
// PRIVACY POLICY CONTENT (v1.0 — April 2026)
// ============================================

export const PrivacyPolicyContent = () => (
  <div>
    <p className="text-zinc-500 text-[10px] tracking-widest uppercase mb-4">Portal de Proveedores — Version 1.0 — Abril 2026</p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">1. Responsable del tratamiento</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      DIGITAL ADVERTISING SOCIAL SERVICES S.L. (en adelante, "DAZZ CREATIVE" o "la Empresa"), con CIF B-XXXXXXXX y domicilio social en Madrid, España, es la entidad responsable del tratamiento de los datos personales recogidos a través del Portal de Proveedores (en adelante, "el Portal").
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      Contacto del Delegado de Protección de Datos: <span className="text-amber-500">dpo@dazzcreative.com</span>
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">2. Datos personales recogidos</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">A través del Portal, DAZZ CREATIVE recoge y trata los siguientes datos personales de los proveedores:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li><strong className="text-zinc-300">Datos identificativos:</strong> nombre completo o razón social, NIF/CIF, dirección postal, teléfono de contacto, dirección de correo electrónico.</li>
      <li><strong className="text-zinc-300">Datos bancarios:</strong> número de cuenta IBAN y certificado bancario asociado, necesarios para la gestión de pagos.</li>
      <li><strong className="text-zinc-300">Datos fiscales:</strong> información contenida en las facturas emitidas por el proveedor (base imponible, IVA, IRPF, importes totales).</li>
      <li><strong className="text-zinc-300">Datos de acceso:</strong> credenciales de acceso al Portal (email y contraseña cifrada).</li>
      <li><strong className="text-zinc-300">Datos de actividad:</strong> historial de facturas, notificaciones, y acciones realizadas en el Portal.</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">3. Finalidad del tratamiento</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">Los datos personales se tratan con las siguientes finalidades:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li><strong className="text-zinc-300">Gestión de la relación comercial:</strong> registro y administración de proveedores, tramitación de facturas, gestión de pagos y comunicaciones operativas.</li>
      <li><strong className="text-zinc-300">Cumplimiento de obligaciones legales:</strong> obligaciones fiscales y contables conforme a la normativa española vigente (Ley General Tributaria, Código de Comercio).</li>
      <li><strong className="text-zinc-300">Verificación de identidad:</strong> validación de datos bancarios y fiscales mediante certificados y verificación automatizada.</li>
      <li><strong className="text-zinc-300">Comunicaciones relacionadas con el servicio:</strong> notificaciones sobre el estado de facturas, aprobaciones, pagos y cambios en la cuenta del proveedor.</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">4. Base legal del tratamiento</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">El tratamiento de datos se fundamenta en:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li><strong className="text-zinc-300">Ejecución de contrato:</strong> el tratamiento es necesario para la gestión de la relación contractual entre DAZZ CREATIVE y el proveedor (Art. 6.1.b RGPD).</li>
      <li><strong className="text-zinc-300">Obligación legal:</strong> conservación de datos fiscales y contables conforme a la legislación española (Art. 6.1.c RGPD).</li>
      <li><strong className="text-zinc-300">Interés legítimo:</strong> prevención de fraude y seguridad del sistema (Art. 6.1.f RGPD).</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">5. Conservación de datos</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">Los datos personales se conservarán durante los siguientes plazos:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-3 list-disc list-inside space-y-1">
      <li><strong className="text-zinc-300">Datos fiscales y contables:</strong> 6 años desde el último ejercicio fiscal en que se utilizaron, conforme al artículo 30 del Código de Comercio y la Ley General Tributaria.</li>
      <li><strong className="text-zinc-300">Datos de la relación comercial:</strong> mientras se mantenga la relación activa con el proveedor y durante el plazo legal de conservación posterior.</li>
      <li><strong className="text-zinc-300">Datos de acceso al Portal:</strong> mientras la cuenta del proveedor permanezca activa. En caso de desactivación, los datos se conservarán conforme a los plazos legales indicados.</li>
    </ul>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      La desactivación de la cuenta del proveedor no implica la eliminación de datos sujetos a obligación legal de conservación.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">6. Destinatarios de los datos</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">Los datos personales podrán ser comunicados a:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li><strong className="text-zinc-300">Proveedores de servicios tecnológicos:</strong> plataformas de alojamiento (Railway, Vercel), almacenamiento en la nube (Cloudinary, Cloudflare), procesamiento de inteligencia artificial (Anthropic), y servicios de correo electrónico (Brevo). Todos los proveedores cumplen con el RGPD o disponen de cláusulas contractuales tipo.</li>
      <li><strong className="text-zinc-300">Administraciones públicas:</strong> cuando sea requerido por obligación legal (Agencia Tributaria, Seguridad Social).</li>
      <li><strong className="text-zinc-300">Entidades del grupo DAZZ:</strong> DAZZ CREATIVE AUDIOVISUAL S.L. y entidades vinculadas, para la gestión administrativa y contable interna.</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">7. Derechos del interesado</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">El proveedor tiene derecho a:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-3 list-disc list-inside space-y-1">
      <li><strong className="text-zinc-300">Acceso:</strong> conocer qué datos personales se están tratando.</li>
      <li><strong className="text-zinc-300">Rectificación:</strong> solicitar la corrección de datos inexactos o incompletos.</li>
      <li><strong className="text-zinc-300">Supresión:</strong> solicitar la eliminación de datos cuando ya no sean necesarios, sin perjuicio de las obligaciones legales de conservación.</li>
      <li><strong className="text-zinc-300">Limitación del tratamiento:</strong> solicitar la restricción del tratamiento en los casos previstos legalmente.</li>
      <li><strong className="text-zinc-300">Portabilidad:</strong> recibir los datos en un formato estructurado y de uso común.</li>
      <li><strong className="text-zinc-300">Oposición:</strong> oponerse al tratamiento basado en interés legítimo.</li>
    </ul>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      Para ejercer estos derechos, el proveedor puede dirigirse a: <span className="text-amber-500">dpo@dazzcreative.com</span> indicando su identidad y el derecho que desea ejercer.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      Asimismo, el interesado tiene derecho a presentar una reclamación ante la Agencia Española de Protección de Datos (www.aepd.es) si considera que sus derechos no han sido debidamente atendidos.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">8. Medidas de seguridad</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">DAZZ CREATIVE aplica las medidas técnicas y organizativas apropiadas para garantizar la seguridad de los datos personales, incluyendo:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li>Cifrado de datos sensibles (IBAN) mediante algoritmo AES-128 (Fernet).</li>
      <li>Certificados bancarios almacenados en infraestructura segura con acceso restringido.</li>
      <li>Contraseñas almacenadas con hash bcrypt, nunca en texto plano.</li>
      <li>Comunicaciones cifradas mediante HTTPS/TLS.</li>
      <li>Control de acceso basado en roles con autenticación JWT.</li>
      <li>Protección contra ataques de fuerza bruta con bloqueo de cuenta y rate limiting.</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">9. Tratamiento automatizado</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      El Portal utiliza sistemas de inteligencia artificial para la extracción automática de datos de facturas y la verificación de datos bancarios. Estas decisiones automatizadas no producen efectos jurídicos sobre el proveedor y están sujetas a revisión manual por parte del equipo de DAZZ CREATIVE.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      El proveedor tiene derecho a solicitar la intervención humana, expresar su punto de vista y impugnar cualquier decisión basada únicamente en el tratamiento automatizado.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">10. Modificaciones</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      DAZZ CREATIVE se reserva el derecho de modificar la presente Política de Privacidad. En caso de modificación sustancial, se notificará al proveedor a través del Portal y/o por correo electrónico. La continuación del uso del Portal tras la notificación implica la aceptación de las modificaciones.
    </p>
    <p className="text-zinc-500 text-[10px] mb-3">Última actualización: abril de 2026.</p>
    <p className="text-zinc-600 text-[10px] text-center pt-3 border-t border-zinc-800">DAZZ CREATIVE &copy; 2026 — Todos los derechos reservados</p>
  </div>
);


// ============================================
// AGENCY CONTRACT CONTENT (v1.0 — April 2026)
// ============================================

export const AgencyContractContent = () => (
  <div>
    <p className="text-zinc-500 text-[10px] tracking-widest uppercase mb-4">Version 1.0 — Abril 2026</p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">1. Partes contratantes</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      <strong className="text-zinc-300">De una parte,</strong> DAZZLE MANAGEMENT S.L. (en adelante, "la Agencia" o "DAZZLE MGMT"), con CIF B-XXXXXXXX y domicilio social en Madrid, España, representada por D./Dña. _________________, en calidad de Administrador/a.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      <strong className="text-zinc-300">De otra parte,</strong> el/la Talento cuyas datos se detallan en el formulario de registro del Portal de Proveedores de DAZZ CREATIVE (en adelante, "el Talento" o "el Influencer"), identificado/a mediante su NIF/CIF y datos de contacto proporcionados durante el proceso de alta.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">2. Objeto del contrato</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">El presente contrato tiene por objeto regular la relación de representación y gestión comercial entre la Agencia y el Talento, en virtud de la cual:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li>La Agencia actuará como intermediaria y representante del Talento para la obtención, negociación y gestión de colaboraciones comerciales, campañas publicitarias y proyectos de creación de contenido digital.</li>
      <li>El Talento se compromete a prestar sus servicios profesionales de creación de contenido conforme a las condiciones acordadas para cada proyecto individual.</li>
      <li>La gestión administrativa, fiscal y de facturación se realizará a través del Portal de Proveedores de DAZZ CREATIVE.</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">3. Duración</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      El presente contrato tendrá una duración de UN (1) AÑO desde la fecha de aceptación digital en el Portal de Proveedores, renovándose automáticamente por períodos iguales salvo notificación en contrario por cualquiera de las partes con un preaviso mínimo de TREINTA (30) días naturales antes de la fecha de vencimiento.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      La notificación de no renovación podrá realizarse a través del Portal de Proveedores (solicitud de desactivación de cuenta) o por escrito dirigido a la otra parte.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">4. Obligaciones de la Agencia</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">La Agencia se compromete a:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li>Buscar activamente oportunidades comerciales adecuadas al perfil del Talento.</li>
      <li>Negociar las condiciones económicas y contractuales de cada colaboración en interés del Talento.</li>
      <li>Gestionar la facturación y el cobro de los servicios prestados por el Talento, a través del sistema de autofacturación del Portal cuando corresponda.</li>
      <li>Informar al Talento de todas las oportunidades, condiciones y pagos de forma transparente y en tiempo razonable.</li>
      <li>Garantizar el cumplimiento de la normativa fiscal aplicable en la emisión de facturas y la retención de impuestos.</li>
      <li>Proteger los datos personales del Talento conforme a la Política de Privacidad del Portal y al Reglamento General de Protección de Datos (RGPD).</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">5. Obligaciones del Talento</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">El Talento se compromete a:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-4 list-disc list-inside space-y-1">
      <li>Prestar los servicios acordados para cada proyecto con profesionalidad, puntualidad y conforme a las especificaciones del cliente.</li>
      <li>Mantener actualizados sus datos personales, fiscales y bancarios en el Portal de Proveedores.</li>
      <li>Comunicar a la Agencia cualquier acuerdo o negociación directa con marcas o empresas que pudiera entrar en conflicto con la presente relación de representación.</li>
      <li>No aceptar colaboraciones comerciales gestionadas por la Agencia directamente con el cliente, sin la intermediación de ésta.</li>
      <li>Subir las facturas correspondientes a sus servicios a través del Portal de Proveedores en los plazos establecidos.</li>
      <li>Cumplir con las obligaciones fiscales que le correspondan como profesional autónomo o entidad mercantil.</li>
    </ul>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">6. Condiciones económicas</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1"><strong className="text-zinc-300">6.1 Comisión de la Agencia:</strong> La Agencia percibirá una comisión del ___% sobre el importe bruto facturado por cada colaboración gestionada. Esta comisión se deducirá antes de la liquidación al Talento.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1"><strong className="text-zinc-300">6.2 Facturación:</strong> Las facturas se gestionarán a través del Portal de Proveedores. La Agencia podrá emitir autofacturas en nombre del Talento cuando así se acuerde.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1"><strong className="text-zinc-300">6.3 Plazos de pago:</strong> Los pagos al Talento se realizarán en un plazo máximo de TREINTA (30) días desde la recepción del pago del cliente por parte de la Agencia.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4"><strong className="text-zinc-300">6.4 Retenciones fiscales:</strong> Se aplicarán las retenciones de IRPF que correspondan según la normativa vigente. El Talento será responsable de sus obligaciones tributarias como profesional independiente.</p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">7. Propiedad intelectual</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1">7.1 El contenido creado por el Talento en el marco de las colaboraciones gestionadas se regirá por los acuerdos específicos de cada proyecto con el cliente final.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1">7.2 Salvo acuerdo expreso en contrario, el Talento conserva los derechos morales sobre su contenido original.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">7.3 La Agencia podrá utilizar el nombre, imagen y extractos del contenido del Talento con fines promocionales de la propia Agencia, previa notificación al Talento.</p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">8. Confidencialidad</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      Ambas partes se comprometen a mantener la confidencialidad sobre los términos económicos de este contrato, las condiciones de las colaboraciones comerciales, y cualquier información de carácter reservado a la que tengan acceso en el desarrollo de la relación contractual.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      Esta obligación de confidencialidad se mantendrá vigente durante la duración del contrato y durante DOS (2) años tras su finalización.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">9. Exclusividad</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1">9.1 El Talento concede a la Agencia la exclusividad de representación para las categorías y mercados acordados durante la vigencia del contrato.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-1">9.2 El Talento podrá mantener colaboraciones directas en categorías no cubiertas por la Agencia, siempre que informe previamente a ésta.</p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">9.3 En caso de que el Talento reciba ofertas directas de marcas o empresas en categorías gestionadas por la Agencia, deberá redirigirlas a ésta para su gestión.</p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">10. Resolución del contrato</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-2">El contrato podrá resolverse por las siguientes causas:</p>
    <ul className="text-zinc-400 text-xs leading-relaxed mb-3 list-disc list-inside space-y-1">
      <li>Por mutuo acuerdo de las partes, comunicado por escrito o a través del Portal.</li>
      <li>Por incumplimiento grave de las obligaciones contractuales por cualquiera de las partes.</li>
      <li>Por decisión unilateral de cualquiera de las partes, con un preaviso de TREINTA (30) días.</li>
      <li>Por solicitud de desactivación de cuenta en el Portal de Proveedores.</li>
    </ul>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      En caso de resolución, la Agencia liquidará al Talento los importes pendientes en un plazo máximo de SESENTA (60) días. Las obligaciones de confidencialidad y las relativas a proyectos en curso subsistirán tras la resolución.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">11. Protección de datos</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      El tratamiento de datos personales del Talento se rige por la Política de Privacidad del Portal de Proveedores de DAZZ CREATIVE, que el Talento declara haber leído y aceptado.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      La Agencia se compromete a tratar los datos del Talento exclusivamente para las finalidades descritas en dicha Política y conforme al Reglamento (UE) 2016/679 (RGPD) y la Ley Orgánica 3/2018 (LOPDGDD).
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">12. Legislación aplicable y jurisdicción</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-4">
      El presente contrato se rige por la legislación española. Para la resolución de cualquier controversia derivada del mismo, las partes se someten a los Juzgados y Tribunales de Madrid, con renuncia expresa a cualquier otro fuero que pudiera corresponderles.
    </p>

    <h3 className="text-zinc-100 font-semibold text-sm mb-2">13. Aceptación digital</h3>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      La aceptación del presente contrato mediante el Portal de Proveedores de DAZZ CREATIVE tiene la misma validez que la firma manuscrita, conforme a la Ley 34/2002 de Servicios de la Sociedad de la Información y la Ley 59/2003 de Firma Electrónica.
    </p>
    <p className="text-zinc-400 text-xs leading-relaxed mb-3">
      Al completar el proceso de registro y aceptar este documento, el Talento declara haber leído, comprendido y aceptado todas las cláusulas del presente contrato.
    </p>
    <p className="text-zinc-600 text-[10px] text-center pt-3 border-t border-zinc-800">DAZZLE MANAGEMENT S.L. &copy; 2026 — Todos los derechos reservados</p>
  </div>
);


// ============================================
// LEGAL DOCUMENT MODAL
// ============================================

export const LegalDocumentModal = ({ title, children, pdfUrl, onAccept, onClose }) => {
  const [hasScrolledToBottom, setHasScrolledToBottom] = useState(false);
  const scrollRef = useRef(null);

  useEscapeKey(onClose);

  // Auto-enable accept if content is short enough to not need scrolling
  useEffect(() => {
    const el = scrollRef.current;
    if (el && el.scrollHeight <= el.clientHeight + 20) {
      setHasScrolledToBottom(true);
    }
  }, []);

  const handleScroll = (e) => {
    const { scrollTop, clientHeight, scrollHeight } = e.target;
    if (scrollTop + clientHeight >= scrollHeight - 20) {
      setHasScrolledToBottom(true);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-zinc-900 rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-800">
          <h2 className="font-['Bebas_Neue'] text-lg tracking-wider text-zinc-100">{title}</h2>
          <button onClick={onClose} className="text-zinc-500 hover:text-zinc-300 transition-colors">
            <X size={18} />
          </button>
        </div>

        {/* Body — scrollable */}
        <div ref={scrollRef} onScroll={handleScroll} className="max-h-[60vh] overflow-y-auto px-6 py-4">
          {children}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-zinc-800">
          <a href={pdfUrl} download className="inline-flex items-center gap-1.5 border border-zinc-700 text-zinc-300 text-xs px-3.5 py-2 rounded-md hover:bg-zinc-800 transition-colors">
            <Download size={13} /> Download PDF
          </a>
          <div className="flex items-center gap-2">
            {!hasScrolledToBottom && (
              <span className="text-zinc-500 text-[10px]">(scroll to read)</span>
            )}
            <button
              onClick={() => { onAccept(); onClose(); }}
              disabled={!hasScrolledToBottom}
              className="bg-amber-500 hover:bg-amber-400 text-zinc-950 font-bold text-xs px-5 py-2 rounded-md transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Accept
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
