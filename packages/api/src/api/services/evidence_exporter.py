"""Evidence Exporter Service.

Exports evidence events in various formats for compliance reporting.
"""

import csv
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ExportOptions:
    """Options for evidence export."""

    format: str = "json"  # json, csv, pdf
    start_date: datetime | None = None
    end_date: datetime | None = None
    event_types: list[str] | None = None
    include_metadata: bool = True


@dataclass
class ExportResult:
    """Result of an evidence export."""

    success: bool
    format: str
    content: bytes
    filename: str
    content_type: str
    record_count: int
    error: str | None = None


class EvidenceExporter:
    """Export evidence events in various formats.

    Supports:
    - JSON: Full structured data export
    - CSV: Spreadsheet-compatible format
    - PDF: Formatted compliance report (requires reportlab)
    """

    def __init__(self):
        """Initialize evidence exporter."""
        self._pdf_available = False
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate
            self._pdf_available = True
        except ImportError:
            logger.info("reportlab not installed, PDF export disabled")

    async def export(
        self,
        app_id: str,
        org_id: str,
        options: ExportOptions,
    ) -> ExportResult:
        """Export evidence events.

        Args:
            app_id: Application ID to export for
            org_id: Organization ID
            options: Export options

        Returns:
            ExportResult with content and metadata
        """
        try:
            # Fetch evidence events
            events = await self._fetch_events(app_id, options)

            if options.format == "json":
                return self._export_json(events, app_id)
            elif options.format == "csv":
                return self._export_csv(events, app_id)
            elif options.format == "pdf":
                return await self._export_pdf(events, app_id, org_id)
            else:
                return ExportResult(
                    success=False,
                    format=options.format,
                    content=b"",
                    filename="",
                    content_type="",
                    record_count=0,
                    error=f"Unsupported format: {options.format}",
                )

        except Exception as e:
            logger.exception(f"Export failed: {e}")
            return ExportResult(
                success=False,
                format=options.format,
                content=b"",
                filename="",
                content_type="",
                record_count=0,
                error=str(e),
            )

    async def _fetch_events(
        self,
        app_id: str,
        options: ExportOptions,
    ) -> list[dict[str, Any]]:
        """Fetch evidence events from database.

        Args:
            app_id: Application ID
            options: Export options with filters

        Returns:
            List of evidence events
        """
        from api.db import supabase

        if not supabase:
            return []

        query = (
            supabase.table("evidence_events")
            .select("*")
            .eq("app_id", app_id)
            .order("created_at", desc=True)
        )

        # Apply date filters
        if options.start_date:
            query = query.gte("created_at", options.start_date.isoformat())
        if options.end_date:
            query = query.lte("created_at", options.end_date.isoformat())

        # Apply event type filter
        if options.event_types:
            query = query.in_("event_type", options.event_types)

        result = query.execute()
        return result.data or []

    def _export_json(
        self,
        events: list[dict],
        app_id: str,
    ) -> ExportResult:
        """Export events as JSON.

        Args:
            events: List of events
            app_id: Application ID

        Returns:
            ExportResult with JSON content
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_export_{app_id[:8]}_{timestamp}.json"

        export_data = {
            "export_metadata": {
                "app_id": app_id,
                "exported_at": datetime.utcnow().isoformat(),
                "record_count": len(events),
                "format_version": "1.0",
            },
            "events": events,
        }

        content = json.dumps(export_data, indent=2, default=str).encode("utf-8")

        return ExportResult(
            success=True,
            format="json",
            content=content,
            filename=filename,
            content_type="application/json",
            record_count=len(events),
        )

    def _export_csv(
        self,
        events: list[dict],
        app_id: str,
    ) -> ExportResult:
        """Export events as CSV.

        Args:
            events: List of events
            app_id: Application ID

        Returns:
            ExportResult with CSV content
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"evidence_export_{app_id[:8]}_{timestamp}.csv"

        # Define CSV columns
        columns = [
            "id",
            "event_type",
            "created_at",
            "actor_email",
            "actor_id",
            "ip_address",
            "title",
            "description",
            "severity",
        ]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()

        for event in events:
            # Flatten the data field for CSV
            data = event.get("data", {})
            row = {
                "id": event.get("id", ""),
                "event_type": event.get("event_type", ""),
                "created_at": event.get("created_at", ""),
                "actor_email": event.get("actor_email", ""),
                "actor_id": event.get("actor_id", ""),
                "ip_address": event.get("ip_address", ""),
                "title": data.get("title", ""),
                "description": data.get("description", ""),
                "severity": data.get("severity", "info"),
            }
            writer.writerow(row)

        content = output.getvalue().encode("utf-8")

        return ExportResult(
            success=True,
            format="csv",
            content=content,
            filename=filename,
            content_type="text/csv",
            record_count=len(events),
        )

    async def _export_pdf(
        self,
        events: list[dict],
        app_id: str,
        org_id: str,
    ) -> ExportResult:
        """Export events as PDF report.

        Args:
            events: List of events
            app_id: Application ID
            org_id: Organization ID

        Returns:
            ExportResult with PDF content
        """
        if not self._pdf_available:
            return ExportResult(
                success=False,
                format="pdf",
                content=b"",
                filename="",
                content_type="",
                record_count=0,
                error="PDF export requires reportlab. Install with: pip install reportlab",
            )

        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import letter
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.lib.units import inch
            from reportlab.platypus import (
                Paragraph,
                SimpleDocTemplate,
                Spacer,
                Table,
                TableStyle,
            )

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"evidence_report_{app_id[:8]}_{timestamp}.pdf"

            # Create PDF in memory
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []

            # Title
            title_style = ParagraphStyle(
                "CustomTitle",
                parent=styles["Title"],
                fontSize=24,
                spaceAfter=30,
            )
            story.append(Paragraph("Evidence Compliance Report", title_style))
            story.append(Spacer(1, 12))

            # Report metadata
            meta_data = [
                ["Report Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
                ["Application ID:", app_id[:8] + "..."],
                ["Total Events:", str(len(events))],
            ]
            meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
            meta_table.setStyle(TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            story.append(meta_table)
            story.append(Spacer(1, 24))

            # Event summary by type
            story.append(Paragraph("Event Summary by Type", styles["Heading2"]))
            story.append(Spacer(1, 12))

            type_counts: dict[str, int] = {}
            for event in events:
                etype = event.get("event_type", "UNKNOWN")
                type_counts[etype] = type_counts.get(etype, 0) + 1

            if type_counts:
                summary_data = [["Event Type", "Count"]]
                for etype, count in sorted(type_counts.items()):
                    summary_data.append([etype, str(count)])

                summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
                summary_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                ]))
                story.append(summary_table)
                story.append(Spacer(1, 24))

            # Recent events table
            story.append(Paragraph("Recent Events", styles["Heading2"]))
            story.append(Spacer(1, 12))

            if events:
                # Show first 50 events
                display_events = events[:50]
                event_data = [["Date", "Type", "Title"]]

                for event in display_events:
                    created = event.get("created_at", "")[:19].replace("T", " ")
                    etype = event.get("event_type", "")
                    data = event.get("data", {})
                    title = data.get("title", "")[:50]
                    event_data.append([created, etype, title])

                event_table = Table(event_data, colWidths=[1.5 * inch, 1.5 * inch, 3.5 * inch])
                event_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)]),
                ]))
                story.append(event_table)

                if len(events) > 50:
                    story.append(Spacer(1, 12))
                    story.append(Paragraph(
                        f"... and {len(events) - 50} more events (see JSON/CSV export for full list)",
                        styles["Normal"],
                    ))

            # Build PDF
            doc.build(story)
            content = buffer.getvalue()

            return ExportResult(
                success=True,
                format="pdf",
                content=content,
                filename=filename,
                content_type="application/pdf",
                record_count=len(events),
            )

        except Exception as e:
            logger.exception(f"PDF generation failed: {e}")
            return ExportResult(
                success=False,
                format="pdf",
                content=b"",
                filename="",
                content_type="",
                record_count=0,
                error=str(e),
            )


# Singleton instance
_exporter: EvidenceExporter | None = None


def get_exporter() -> EvidenceExporter:
    """Get the evidence exporter instance."""
    global _exporter
    if _exporter is None:
        _exporter = EvidenceExporter()
    return _exporter
