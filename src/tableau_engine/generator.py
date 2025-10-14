"""
Tableau Workbook Generation Engine.
Creates actual Tableau workbook files (.twb/.twbx) from AI-generated specifications.
"""

import os
import json
import zipfile
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import uuid

from ..models.schemas import (
    TableauWorkbookSpec, DashboardSpec, WorksheetSpec, 
    VisualizationSpec, KPISpecification, GenerationRequest,
    GenerationResult, VisualizationType, ColorScheme
)
from ..utils.logger import get_logger

logger = get_logger(__name__)

class TableauWorkbookGenerator:
    """
    Generates Tableau workbook files from AI-generated specifications.
    Supports both .twb (XML) and .twbx (packaged) formats.
    """
    
    def __init__(self, output_directory: str = "data/outputs"):
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Tableau version compatibility
        self.tableau_version = "2023.3"
        self.build_version = "20233.23.0322.1437"
        
    def generate_workbook(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate a Tableau workbook from the provided specifications.
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting workbook generation for dataset: {request.dataset_schema.name}")
            
            # Create workbook specification
            workbook_spec = self._create_workbook_specification(request)
            
            # Generate XML content
            workbook_xml = self._generate_workbook_xml(workbook_spec, request)
            
            # Generate data source
            datasource_xml = self._generate_datasource_xml(request.dataset_schema)
            
            # Create output file
            if request.output_format == "twbx":
                file_path = self._create_twbx_file(workbook_xml, datasource_xml, workbook_spec, request)
            else:
                file_path = self._create_twb_file(workbook_xml, workbook_spec)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Workbook generated successfully: {file_path}")
            
            return GenerationResult(
                workbook_spec=workbook_spec,
                file_path=str(file_path),
                generation_time=generation_time,
                warnings=[],
                success=True,
                error_message=None
            )
            
        except Exception as e:
            logger.error(f"Workbook generation failed: {e}")
            return GenerationResult(
                workbook_spec=TableauWorkbookSpec(
                    name="Failed Generation",
                    description="Generation failed",
                    dashboards=[],
                    data_source=""
                ),
                file_path="",
                generation_time=(datetime.now() - start_time).total_seconds(),
                warnings=[],
                success=False,
                error_message=str(e)
            )
    
    def _create_workbook_specification(self, request: GenerationRequest) -> TableauWorkbookSpec:
        """Create a complete workbook specification from the AI analysis"""
        
        # Create worksheets from AI recommendations
        worksheets = []
        for i, viz_spec in enumerate(request.ai_analysis.recommended_visualizations):
            worksheet = WorksheetSpec(
                name=f"Sheet {i+1}",
                visualization=viz_spec,
                kpis=[],
                description=f"Generated visualization: {viz_spec.title}"
            )
            worksheets.append(worksheet)
        
        # Create a main dashboard
        dashboard = DashboardSpec(
            name="AI Generated Dashboard",
            description="Automatically generated dashboard based on AI analysis",
            worksheets=worksheets,
            color_scheme=ColorScheme.TABLEAU10
        )
        
        # Create workbook specification
        workbook_spec = TableauWorkbookSpec(
            name=request.dataset_schema.name + "_Dashboard",
            description=f"AI-generated dashboard for {request.dataset_schema.name}",
            dashboards=[dashboard],
            data_source=request.dataset_schema.name,
            version=self.tableau_version
        )
        
        return workbook_spec
    
    def _generate_workbook_xml(self, workbook_spec: TableauWorkbookSpec, request: GenerationRequest) -> str:
        """Generate the main workbook XML content"""
        
        # Create root workbook element
        workbook = Element("workbook")
        workbook.set("version", self.tableau_version)
        workbook.set("build-version", self.build_version)
        workbook.set("source-build", self.build_version)
        
        # Add document preferences
        preferences = SubElement(workbook, "preferences")
        
        # Add repository location (for local files)
        repository = SubElement(workbook, "repository-location")
        repository.set("id", "TWB Repository")
        repository.set("path", f"{workbook_spec.name}.twb")
        
        # Add datasources
        datasources = SubElement(workbook, "datasources")
        datasource = self._create_datasource_element(datasources, request.dataset_schema)
        
        # Add worksheets
        worksheets = SubElement(workbook, "worksheets")
        for dashboard in workbook_spec.dashboards:
            for worksheet in dashboard.worksheets:
                self._create_worksheet_element(worksheets, worksheet, datasource)
        
        # Add dashboards
        dashboards = SubElement(workbook, "dashboards")
        for dashboard_spec in workbook_spec.dashboards:
            self._create_dashboard_element(dashboards, dashboard_spec)
        
        # Add windows (for Tableau Desktop compatibility)
        windows = SubElement(workbook, "windows")
        self._create_windows_element(windows, workbook_spec)
        
        # Convert to formatted XML string
        rough_string = tostring(workbook, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _create_datasource_element(self, parent: Element, dataset_schema) -> Element:
        """Create datasource XML element"""
        datasource = SubElement(parent, "datasource")
        datasource.set("caption", dataset_schema.name)
        datasource.set("name", f"federated.{self._generate_id()}")
        datasource.set("version", "18.1")
        
        # Add connection
        connection = SubElement(datasource, "connection")
        connection.set("class", "federated")
        
        # Add named connections
        named_connections = SubElement(connection, "named-connections")
        named_connection = SubElement(named_connections, "named-connection")
        named_connection.set("caption", dataset_schema.name)
        named_connection.set("name", "textscan")
        
        # Add actual connection details
        inner_connection = SubElement(named_connection, "connection")
        inner_connection.set("class", "textscan")
        inner_connection.set("directory", str(self.output_directory))
        inner_connection.set("filename", f"{dataset_schema.name}.csv")
        inner_connection.set("password", "")
        inner_connection.set("server", "")
        
        # Add relation (table structure)
        relation = SubElement(connection, "relation")
        relation.set("connection", "textscan")
        relation.set("name", f"{dataset_schema.name}.csv")
        relation.set("table", f"[{dataset_schema.name}.csv]")
        relation.set("type", "table")
        
        # Add column metadata
        metadata_records = SubElement(datasource, "metadata-records")
        for i, column in enumerate(dataset_schema.columns):
            self._add_column_metadata(metadata_records, column, i)
        
        # Add column instances
        column_instances = SubElement(datasource, "column-instances")
        for column in dataset_schema.columns:
            column_instance = SubElement(column_instances, "column-instance")
            column_instance.set("column", f"[{column.name}]")
            column_instance.set("derivation", "None")
            column_instance.set("name", f"[{column.name}]")
            column_instance.set("pivot", "key")
            column_instance.set("type", "nominal" if column.recommended_role == "dimension" else "quantitative")
        
        return datasource
    
    def _add_column_metadata(self, parent: Element, column, ordinal: int):
        """Add metadata for a single column"""
        metadata = SubElement(parent, "metadata-record")
        metadata.set("class", "column")
        
        # Add remote properties
        remote_name = SubElement(metadata, "remote-name")
        remote_name.text = column.name
        
        remote_type = SubElement(metadata, "remote-type")
        remote_type.text = self._get_tableau_data_type(column.data_type)
        
        local_name = SubElement(metadata, "local-name")
        local_name.text = f"[{column.name}]"
        
        # Add parent name and remote alias
        parent_name = SubElement(metadata, "parent-name")
        parent_name.text = f"[{column.name}]"
        
        remote_alias = SubElement(metadata, "remote-alias")
        remote_alias.text = column.name
        
        ordinal_elem = SubElement(metadata, "ordinal")
        ordinal_elem.text = str(ordinal)
        
        # Add local type
        local_type = SubElement(metadata, "local-type")
        local_type.text = self._get_tableau_data_type(column.data_type)
        
        # Add aggregation
        aggregation = SubElement(metadata, "aggregation")
        aggregation.text = "Sum" if column.recommended_role == "measure" else "Count"
        
        # Add contains null
        contains_null = SubElement(metadata, "contains-null")
        contains_null.text = "true" if column.null_count > 0 else "false"
    
    def _get_tableau_data_type(self, data_type) -> str:
        """Convert our data type to Tableau data type"""
        mapping = {
            "integer": "integer",
            "float": "real",
            "string": "string",
            "datetime": "datetime",
            "boolean": "boolean",
            "categorical": "string"
        }
        return mapping.get(data_type.value, "string")
    
    def _create_worksheet_element(self, parent: Element, worksheet_spec: WorksheetSpec, datasource: Element):
        """Create worksheet XML element"""
        worksheet = SubElement(parent, "worksheet")
        worksheet.set("name", worksheet_spec.name)
        
        # Add table element
        table = SubElement(worksheet, "table")
        table.set("name", worksheet_spec.name)
        table.set("show-empty", "true")
        
        # Add view element
        view = SubElement(table, "view")
        
        # Add datasources reference
        datasources = SubElement(view, "datasources")
        datasource_ref = SubElement(datasources, "datasource")
        datasource_ref.set("caption", datasource.get("caption"))
        datasource_ref.set("name", datasource.get("name"))
        
        # Add visualization-specific elements
        self._add_visualization_elements(view, worksheet_spec.visualization, datasource)
        
        # Add style elements
        self._add_worksheet_style(worksheet, worksheet_spec)
    
    def _add_visualization_elements(self, view: Element, viz_spec: VisualizationSpec, datasource: Element):
        """Add visualization-specific XML elements"""
        
        # Add aggregation
        aggregation = SubElement(view, "aggregation")
        aggregation.set("value", "true")
        
        # Add panes
        panes = SubElement(view, "panes")
        pane = SubElement(panes, "pane")
        pane.set("selection-relaxation-option", "selection-relaxation-allow")
        
        # Add view name
        view_name = SubElement(pane, "view")
        view_name.set("name", viz_spec.title)
        
        # Add mark elements based on chart type
        mark = SubElement(pane, "mark")
        mark.set("class", self._get_tableau_mark_type(viz_spec.chart_type))
        
        # Add encodings
        encodings = SubElement(pane, "encodings")
        
        # Add rows encoding
        if viz_spec.y_axis:
            for field in viz_spec.y_axis:
                self._add_encoding(encodings, "rows", field, datasource, viz_spec.aggregation_type)
        
        # Add columns encoding  
        if viz_spec.x_axis:
            for field in viz_spec.x_axis:
                self._add_encoding(encodings, "columns", field, datasource, "none")
        
        # Add color encoding
        if viz_spec.color_field:
            self._add_encoding(encodings, "color", viz_spec.color_field, datasource, "none")
        
        # Add size encoding
        if viz_spec.size_field:
            self._add_encoding(encodings, "size", viz_spec.size_field, datasource, viz_spec.aggregation_type)
    
    def _add_encoding(self, parent: Element, shelf: str, field_name: str, datasource: Element, aggregation: str):
        """Add field encoding to a shelf"""
        encoding = SubElement(parent, shelf)
        column = SubElement(encoding, "column")
        column.text = f"[{datasource.get('name')}].[{field_name}]"
        
        if aggregation and aggregation != "none":
            column.set("aggregation", aggregation.title())
    
    def _get_tableau_mark_type(self, chart_type: VisualizationType) -> str:
        """Convert visualization type to Tableau mark type"""
        mapping = {
            VisualizationType.BAR: "Bar",
            VisualizationType.LINE: "Line", 
            VisualizationType.AREA: "Area",
            VisualizationType.SCATTER: "Circle",
            VisualizationType.PIE: "Pie",
            VisualizationType.HEATMAP: "Square",
            VisualizationType.TREEMAP: "Square",
            VisualizationType.MAP: "Map"
        }
        return mapping.get(chart_type, "Automatic")
    
    def _create_dashboard_element(self, parent: Element, dashboard_spec: DashboardSpec):
        """Create dashboard XML element"""
        dashboard = SubElement(parent, "dashboard")
        dashboard.set("name", dashboard_spec.name)
        
        # Add size
        size = SubElement(dashboard, "size")
        size.set("maxheight", str(dashboard_spec.dimensions["height"]))
        size.set("maxwidth", str(dashboard_spec.dimensions["width"]))
        
        # Add view
        view = SubElement(dashboard, "view")
        
        # Add zones for layout
        zones = SubElement(view, "zones")
        
        # Create zones for each worksheet
        for i, worksheet in enumerate(dashboard_spec.worksheets):
            zone = SubElement(zones, "zone")
            zone.set("id", str(i))
            zone.set("type", "layout-basic")
            
            # Add zone properties
            self._add_zone_properties(zone, worksheet, i, len(dashboard_spec.worksheets))
        
        # Add device layouts
        devicelayouts = SubElement(view, "devicelayouts")
        devicelayout = SubElement(devicelayouts, "devicelayout")
        devicelayout.set("auto-generated", "true")
        devicelayout.set("name", "Phone")
    
    def _add_zone_properties(self, zone: Element, worksheet: WorksheetSpec, index: int, total: int):
        """Add properties to a dashboard zone"""
        # Calculate position based on grid layout
        cols = 2 if total > 2 else total
        rows = (total + cols - 1) // cols
        
        col = index % cols
        row = index // cols
        
        # Set zone dimensions
        zone.set("x", str(col * 400))
        zone.set("y", str(row * 300))
        zone.set("w", "400")
        zone.set("h", "300")
        
        # Add worksheet reference
        zone_worksheet = SubElement(zone, "worksheet")
        zone_worksheet.set("name", worksheet.name)
    
    def _add_worksheet_style(self, worksheet: Element, worksheet_spec: WorksheetSpec):
        """Add styling elements to worksheet"""
        # Add layout options
        layout_options = SubElement(worksheet, "layout-options")
        
        # Add title
        title = SubElement(layout_options, "title")
        title_text = SubElement(title, "formatted-text")
        title_run = SubElement(title_text, "run")
        title_run.text = worksheet_spec.visualization.title
    
    def _create_windows_element(self, parent: Element, workbook_spec: TableauWorkbookSpec):
        """Create windows element for Tableau Desktop compatibility"""
        window = SubElement(parent, "window")
        window.set("class", "worksheet")
        window.set("maximized", "true")
        window.set("name", workbook_spec.dashboards[0].worksheets[0].name if workbook_spec.dashboards else "Sheet1")
        
        # Add cards
        cards = SubElement(window, "cards")
        edge_name = SubElement(cards, "edge")
        edge_name.set("name", "left")
        
        # Add strip
        strip = SubElement(edge_name, "strip")
        strip.set("size", "160")
        
        # Add card for data pane
        card = SubElement(strip, "card")
        card.set("type", "data")
    
    def _generate_datasource_xml(self, dataset_schema) -> str:
        """Generate separate datasource XML for .tds file"""
        datasource = Element("datasource")
        datasource.set("formatted-name", dataset_schema.name)
        datasource.set("inline", "true")
        datasource.set("source-platform", "win")
        datasource.set("version", "18.1")
        
        # Add connection details similar to main datasource
        connection = SubElement(datasource, "connection")
        connection.set("class", "textscan")
        connection.set("directory", str(self.output_directory))
        connection.set("filename", f"{dataset_schema.name}.csv")
        
        # Convert to XML string
        rough_string = tostring(datasource, 'unicode')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")
    
    def _create_twb_file(self, workbook_xml: str, workbook_spec: TableauWorkbookSpec) -> Path:
        """Create a .twb file with the workbook XML"""
        filename = f"{workbook_spec.name}.twb"
        file_path = self.output_directory / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(workbook_xml)
        
        return file_path
    
    def _create_twbx_file(self, workbook_xml: str, datasource_xml: str, 
                         workbook_spec: TableauWorkbookSpec, request: GenerationRequest) -> Path:
        """Create a .twbx (packaged) file with workbook and data"""
        filename = f"{workbook_spec.name}.twbx"
        file_path = self.output_directory / filename
        
        with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add workbook XML
            zipf.writestr("workbook.twb", workbook_xml)
            
            # Add datasource
            zipf.writestr("Data/Datasources/datasource.tds", datasource_xml)
            
            # Add sample data if requested
            if request.include_sample_data:
                sample_data = self._generate_sample_csv(request.dataset_schema)
                zipf.writestr(f"Data/{request.dataset_schema.name}.csv", sample_data)
        
        return file_path
    
    def _generate_sample_csv(self, dataset_schema) -> str:
        """Generate sample CSV data for the dataset"""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = [col.name for col in dataset_schema.columns]
        writer.writerow(headers)
        
        # Write sample data based on column metadata
        for i in range(min(100, dataset_schema.total_rows)):
            row = []
            for col in dataset_schema.columns:
                if col.sample_values:
                    # Use actual sample values if available
                    sample_value = col.sample_values[i % len(col.sample_values)]
                    row.append(sample_value)
                else:
                    # Generate synthetic sample based on data type
                    row.append(self._generate_synthetic_value(col, i))
            writer.writerow(row)
        
        return output.getvalue()
    
    def _generate_synthetic_value(self, column, index: int):
        """Generate synthetic sample value for a column"""
        import random
        
        if column.data_type.value == "integer":
            return random.randint(1, 1000)
        elif column.data_type.value == "float":
            return round(random.uniform(0, 1000), 2)
        elif column.data_type.value == "string":
            return f"{column.name}_{index}"
        elif column.data_type.value == "categorical":
            categories = ["Category A", "Category B", "Category C", "Category D"]
            return random.choice(categories)
        elif column.data_type.value == "datetime":
            from datetime import datetime, timedelta
            base_date = datetime(2023, 1, 1)
            return (base_date + timedelta(days=index)).strftime("%Y-%m-%d")
        elif column.data_type.value == "boolean":
            return random.choice([True, False])
        else:
            return f"Value_{index}"
    
    def _generate_id(self) -> str:
        """Generate a unique ID for Tableau elements"""
        return str(uuid.uuid4()).upper().replace("-", "")[:8]