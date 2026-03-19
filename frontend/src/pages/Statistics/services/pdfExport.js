/**
 * Genera y descarga un informe PDF de IVA reclamable internacional.
 * jsPDF se importa dinámicamente para reducir bundle.
 *
 * @param {Object} params
 * @param {Object} params.data - Datos de estadísticas completas
 * @param {number} params.year - Año seleccionado
 * @param {string|number} params.quarter - Trimestre ('' o 1-4)
 */
import { showWarning } from '../../../utils/toast';

export async function exportPDFReport({ data, year, quarter }) {
  if (!data || !data.foreign_breakdown || data.foreign_breakdown.length === 0) {
    showWarning('No hay datos internacionales para exportar');
    return;
  }

  const { default: jsPDF } = await import('jspdf');
  const doc = new jsPDF();
  const { overview } = data;
  const foreign_breakdown = data.foreign_breakdown.filter(c => c.tax_reclamable_eur > 0);
  const pdfIsAllCompanies = data.mode === 'all_companies';
  const companyLabel = pdfIsAllCompanies
    ? 'TODAS LAS EMPRESAS'
    : (data.company?.company_name || '');

  const colors = {
    primary:   [245, 158, 11],
    secondary: [59, 130, 246],
    success:   [34, 197, 94],
    company:   [124, 58, 237],
    gray:      [161, 161, 170],
    darkGray:  [82, 82, 91],
  };

  const pageHeight = doc.internal.pageSize.height;
  const pageWidth  = doc.internal.pageSize.width;
  let yPos = 20;

  const checkPageBreak = (space) => {
    if (yPos + space > pageHeight - 20) { doc.addPage(); yPos = 20; }
  };
  const drawBox = (x, y, w, h, fill) => {
    doc.setFillColor(...fill); doc.rect(x, y, w, h, 'F');
  };

  // HEADER
  drawBox(0, 0, pageWidth, 50, [24, 24, 27]);
  doc.setTextColor(255, 255, 255);
  doc.setFontSize(22); doc.setFont(undefined, 'bold');
  doc.text('INFORME IVA RECLAMABLE', pageWidth / 2, 18, { align: 'center' });
  doc.setFontSize(12); doc.setFont(undefined, 'normal');
  doc.text(`Ano ${year}${quarter ? ` · Q${quarter}` : ''}`, pageWidth / 2, 28, { align: 'center' });
  doc.setFontSize(10);
  doc.text(companyLabel, pageWidth / 2, 37, { align: 'center' });
  doc.setFontSize(8); doc.setTextColor(...colors.gray);
  doc.text(`Generado: ${new Date().toLocaleDateString('es-ES')}`, pageWidth / 2, 44, { align: 'center' });
  yPos = 60;
  doc.setTextColor(0, 0, 0);

  // RESUMEN
  checkPageBreak(45);
  drawBox(15, yPos - 5, pageWidth - 30, 38, [254, 243, 199]);
  doc.setFontSize(12); doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.primary);
  doc.text('RESUMEN GLOBAL', 20, yPos + 3);
  yPos += 10;
  doc.setFontSize(10); doc.setFont(undefined, 'normal'); doc.setTextColor(0, 0, 0);
  [
    `Total Internacional: ${overview.international_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`,
    `IVA Reclamable: ${overview.iva_reclamable.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`,
    `Pa\u00EDses: ${foreign_breakdown.length}  \u00B7  Proyectos: ${foreign_breakdown.reduce((s, c) => s + c.projects_count, 0)}`,
  ].forEach(line => { doc.text(line, 25, yPos); yPos += 7; });
  yPos += 10;

  // Helper: renderiza un proyecto con sus tickets
  const renderProject = (project, indent) => {
    const tickets = (project.tickets || []).filter(t => t.foreign_tax_eur > 0);

    checkPageBreak(30);
    doc.setDrawColor(...colors.gray); doc.setLineWidth(0.2);
    doc.line(indent, yPos, pageWidth - indent, yPos);
    yPos += 5;

    doc.setFontSize(10); doc.setFont(undefined, 'bold'); doc.setTextColor(0, 0, 0);
    const splitTitle = doc.splitTextToSize(
      `${project.creative_code}  \u2013  ${project.description}`,
      pageWidth - indent * 2 - 5
    );
    doc.text(splitTitle, indent, yPos);
    yPos += splitTitle.length * 6;

    doc.setFontSize(8); doc.setFont(undefined, 'normal'); doc.setTextColor(...colors.darkGray);
    doc.text(
      `Total proyecto: ${project.total_amount.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`,
      indent + 4, yPos
    );
    yPos += 7;

    if (tickets.length > 0) {
      doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.success);
      doc.text(`TICKETS INTERNACIONALES (${tickets.length}):`, indent + 4, yPos);
      yPos += 6; doc.setTextColor(0, 0, 0);

      tickets.forEach((ticket, idx) => {
        checkPageBreak(22);
        drawBox(indent + 4, yPos - 2, pageWidth - (indent + 4) * 2, 20, [249, 250, 251]);

        doc.setFontSize(8); doc.setFont(undefined, 'bold'); doc.setTextColor(0, 0, 0);
        doc.text(`${idx + 1}. ${ticket.provider}`, indent + 7, yPos + 3);
        yPos += 7;

        doc.setFont(undefined, 'normal'); doc.setTextColor(...colors.darkGray);
        doc.text(
          `Fecha: ${ticket.date || 'N/A'}  \u00B7  Total: ${(ticket.foreign_amount || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })} ${ticket.currency}  \u00B7  Factura: ${ticket.invoice_number || 'N/A'}`,
          indent + 7, yPos
        );
        yPos += 5;

        doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.success);
        doc.text(
          `IVA Reclamable: ${(ticket.foreign_tax_eur || 0).toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`,
          indent + 7, yPos
        );
        yPos += 7;
        doc.setTextColor(0, 0, 0);
      });
    }
    yPos += 4;
  };

  // DESGLOSE POR PAIS
  foreign_breakdown.forEach((country) => {
    checkPageBreak(50);

    drawBox(15, yPos - 5, pageWidth - 30, 13, [219, 234, 254]);
    doc.setFontSize(12); doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.secondary);
    doc.text(`${country.country_name}  (${country.currency})`, 20, yPos + 3);
    yPos += 13;
    doc.setFontSize(8); doc.setFont(undefined, 'normal'); doc.setTextColor(...colors.darkGray);
    doc.text(
      `${country.geo_classification}  \u00B7  Total: ${country.total_spent.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC  \u00B7  IVA Reclamable: ${country.tax_reclamable_eur.toLocaleString('es-ES', { minimumFractionDigits: 2 })}\u20AC`,
      20, yPos
    );
    yPos += 10; doc.setTextColor(0, 0, 0);

    if (pdfIsAllCompanies && country.companies?.length > 0) {
      country.companies.forEach((companyGroup) => {
        checkPageBreak(18);
        drawBox(18, yPos - 3, pageWidth - 36, 12, [237, 233, 254]);
        doc.setFontSize(10); doc.setFont(undefined, 'bold'); doc.setTextColor(...colors.company);
        doc.text(`${companyGroup.company_name}`, 24, yPos + 4);
        yPos += 14; doc.setTextColor(0, 0, 0);

        companyGroup.projects.forEach(project => renderProject(project, 24));
        yPos += 4;
      });
    } else {
      (country.projects || []).forEach(project => renderProject(project, 20));
    }

    yPos += 8;
  });

  // FOOTER
  const totalPages = doc.internal.getNumberOfPages();
  for (let i = 1; i <= totalPages; i++) {
    doc.setPage(i);
    doc.setDrawColor(...colors.gray); doc.setLineWidth(0.5);
    doc.line(20, pageHeight - 15, pageWidth - 20, pageHeight - 15);
    doc.setFontSize(8); doc.setFont(undefined, 'italic'); doc.setTextColor(...colors.darkGray);
    doc.text(`P\u00E1gina ${i} de ${totalPages}`, pageWidth / 2, pageHeight - 8, { align: 'center' });
  }

  const safeName = companyLabel.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
  doc.save(`Informe_IVA_${year}${quarter ? `_Q${quarter}` : ''}${safeName ? `_${safeName}` : ''}_${Date.now()}.pdf`);
}
