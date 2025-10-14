"""
Core Pydantic models for the Tableau Dashboard Generator application.
Defines data structures for dashboard specifications, AI responses, and configuration.
"""

from typing import List, Dict, Optional, Any, Union, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum
import pandas as pd
from datetime import datetime

class DataType(str, Enum):
    """Supported data types for analysis"""
    INTEGER = "integer"
    FLOAT = "float"
    STRING = "string"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"

class VisualizationType(str, Enum):
    """Supported Tableau visualization types"""
    BAR = "bar"
    LINE = "line"
    AREA = "area"
    SCATTER = "scatter"
    PIE = "pie"
    HISTOGRAM = "histogram"
    HEATMAP = "heatmap"
    TREEMAP = "treemap"
    MAP = "map"
    FILLED_MAP = "filled_map"
    GANTT = "gantt"
    PACKED_BUBBLES = "packed_bubbles"
    BOX_PLOT = "box_plot"
    BULLET_GRAPH = "bullet_graph"

class ColorScheme(str, Enum):
    """Tableau color schemes"""
    TABLEAU10 = "tableau10"
    TABLEAU20 = "tableau20"
    CATEGORY10 = "category10"
    BLUES = "blues"
    ORANGES = "oranges"
    GREENS = "greens"
    RED_BLUE = "red_blue"
    ORANGE_BLUE = "orange_blue"
    GREEN_ORANGE = "green_orange"

class DataColumn(BaseModel):
    """Represents a single column in the dataset"""
    name: str = Field(..., description="Column name")
    data_type: DataType = Field(..., description="Data type of the column")
    unique_values: int = Field(..., description="Number of unique values")
    null_count: int = Field(0, description="Number of null values")
    sample_values: List[Any] = Field(..., description="Sample values from the column")
    statistics: Optional[Dict[str, float]] = Field(None, description="Statistical summary for numeric columns")
    is_key_field: bool = Field(False, description="Whether this column is identified as a key business field")
    recommended_role: Optional[Literal["dimension", "measure", "attribute"]] = Field(None, description="Recommended Tableau role")

class DatasetSchema(BaseModel):
    """Complete dataset schema and metadata"""
    name: str = Field(..., description="Dataset name")
    total_rows: int = Field(..., description="Total number of rows")
    total_columns: int = Field(..., description="Total number of columns")
    columns: List[DataColumn] = Field(..., description="List of column specifications")
    data_quality_score: float = Field(..., ge=0, le=1, description="Overall data quality score")
    business_context: Optional[str] = Field(None, description="Business context description")
    created_at: datetime = Field(default_factory=datetime.now)

class KPISpecification(BaseModel):
    """Key Performance Indicator specification"""
    name: str = Field(..., description="KPI name")
    description: str = Field(..., description="KPI description")
    calculation: str = Field(..., description="Tableau calculation formula")
    target_value: Optional[float] = Field(None, description="Target value for the KPI")
    format_string: str = Field("#,##0", description="Number format")
    priority: int = Field(1, ge=1, le=5, description="Priority level (1=highest, 5=lowest)")

class VisualizationSpec(BaseModel):
    """Specification for a single visualization"""
    chart_type: VisualizationType = Field(..., description="Type of visualization")
    title: str = Field(..., description="Chart title")
    x_axis: List[str] = Field(..., description="Fields for X-axis")
    y_axis: List[str] = Field(..., description="Fields for Y-axis")
    color_field: Optional[str] = Field(None, description="Field for color encoding")
    size_field: Optional[str] = Field(None, description="Field for size encoding")
    filters: List[Dict[str, Any]] = Field(default_factory=list, description="Applied filters")
    color_scheme: ColorScheme = Field(ColorScheme.TABLEAU10, description="Color scheme to use")
    show_labels: bool = Field(True, description="Whether to show data labels")
    show_legend: bool = Field(True, description="Whether to show legend")
    aggregation_type: Optional[Literal["sum", "avg", "count", "min", "max"]] = Field("sum", description="Aggregation method")

class WorksheetSpec(BaseModel):
    """Specification for a Tableau worksheet"""
    name: str = Field(..., description="Worksheet name")
    visualization: VisualizationSpec = Field(..., description="Visualization specification")
    kpis: List[KPISpecification] = Field(default_factory=list, description="Associated KPIs")
    description: Optional[str] = Field(None, description="Worksheet description")
    dimensions: Dict[str, int] = Field({"width": 800, "height": 600}, description="Worksheet dimensions")

class DashboardLayout(BaseModel):
    """Dashboard layout specification"""
    layout_type: Literal["automatic", "grid", "free_form"] = Field("automatic", description="Layout type")
    rows: int = Field(2, ge=1, description="Number of rows in grid layout")
    columns: int = Field(2, ge=1, description="Number of columns in grid layout")
    worksheet_positions: Dict[str, Dict[str, Union[int, float]]] = Field(
        default_factory=dict, 
        description="Positioning information for worksheets"
    )

class DashboardSpec(BaseModel):
    """Specification for a complete dashboard"""
    name: str = Field(..., description="Dashboard name")
    description: str = Field(..., description="Dashboard description")
    worksheets: List[WorksheetSpec] = Field(..., description="List of worksheets in the dashboard")
    layout: DashboardLayout = Field(default_factory=DashboardLayout, description="Dashboard layout")
    global_filters: List[Dict[str, Any]] = Field(default_factory=list, description="Dashboard-level filters")
    color_scheme: ColorScheme = Field(ColorScheme.TABLEAU10, description="Overall color scheme")
    dimensions: Dict[str, int] = Field({"width": 1200, "height": 800}, description="Dashboard dimensions")

class TableauWorkbookSpec(BaseModel):
    """Complete Tableau workbook specification"""
    name: str = Field(..., description="Workbook name")
    description: str = Field(..., description="Workbook description")
    dashboards: List[DashboardSpec] = Field(..., description="List of dashboards")
    data_source: str = Field(..., description="Data source connection string or file path")
    version: str = Field("2023.3", description="Tableau version compatibility")
    created_by: str = Field("AI Dashboard Generator", description="Creator information")
    created_at: datetime = Field(default_factory=datetime.now)

class AIAnalysisRequest(BaseModel):
    """Request for AI analysis of dataset"""
    dataset_schema: DatasetSchema = Field(..., description="Dataset schema to analyze")
    business_goals: List[str] = Field(..., description="Business goals and objectives")
    target_audience: str = Field(..., description="Target audience for the dashboard")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Technical or business constraints")

class AIRecommendation(BaseModel):
    """AI recommendation for dashboard design"""
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence in the recommendation")
    reasoning: str = Field(..., description="Explanation of the recommendation")
    alternatives: List[str] = Field(default_factory=list, description="Alternative approaches")

class AIAnalysisResponse(BaseModel):
    """Complete AI analysis response"""
    dataset_insights: Dict[str, Any] = Field(..., description="Insights about the dataset")
    recommended_kpis: List[KPISpecification] = Field(..., description="Recommended KPIs")
    recommended_visualizations: List[VisualizationSpec] = Field(..., description="Recommended visualizations")
    dashboard_recommendations: AIRecommendation = Field(..., description="Dashboard design recommendations")
    layout_suggestions: AIRecommendation = Field(..., description="Layout suggestions")
    color_scheme_recommendation: AIRecommendation = Field(..., description="Color scheme recommendations")
    performance_considerations: List[str] = Field(..., description="Performance optimization suggestions")
    generated_at: datetime = Field(default_factory=datetime.now)

class GenerationRequest(BaseModel):
    """Request to generate a Tableau workbook"""
    dataset_schema: DatasetSchema = Field(..., description="Source dataset schema")
    ai_analysis: AIAnalysisResponse = Field(..., description="AI analysis results")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User-specified preferences")
    output_format: Literal["twb", "twbx"] = Field("twbx", description="Output file format")
    include_sample_data: bool = Field(True, description="Whether to include sample data in workbook")

class GenerationResult(BaseModel):
    """Result of workbook generation"""
    workbook_spec: TableauWorkbookSpec = Field(..., description="Generated workbook specification")
    file_path: str = Field(..., description="Path to the generated file")
    generation_time: float = Field(..., description="Time taken to generate (seconds)")
    warnings: List[str] = Field(default_factory=list, description="Generation warnings")
    success: bool = Field(..., description="Whether generation was successful")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")

class ValidationResult(BaseModel):
    """Result of data or specification validation"""
    is_valid: bool = Field(..., description="Whether the validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")

# Utility functions for model validation
def validate_dataframe_schema(df: pd.DataFrame) -> DatasetSchema:
    """Create a DatasetSchema from a pandas DataFrame"""
    columns = []
    
    for col_name in df.columns:
        col_data = df[col_name]
        
        # Determine data type
        if pd.api.types.is_integer_dtype(col_data):
            data_type = DataType.INTEGER
        elif pd.api.types.is_float_dtype(col_data):
            data_type = DataType.FLOAT
        elif pd.api.types.is_datetime64_any_dtype(col_data):
            data_type = DataType.DATETIME
        elif pd.api.types.is_bool_dtype(col_data):
            data_type = DataType.BOOLEAN
        elif col_data.dtype == 'object' and col_data.nunique() < 50:
            data_type = DataType.CATEGORICAL
        else:
            data_type = DataType.STRING
        
        # Calculate statistics
        statistics = None
        if data_type in [DataType.INTEGER, DataType.FLOAT]:
            statistics = {
                "mean": float(col_data.mean()) if not col_data.isna().all() else 0,
                "std": float(col_data.std()) if not col_data.isna().all() else 0,
                "min": float(col_data.min()) if not col_data.isna().all() else 0,
                "max": float(col_data.max()) if not col_data.isna().all() else 0,
            }
        
        # Create column specification
        column_spec = DataColumn(
            name=col_name,
            data_type=data_type,
            unique_values=col_data.nunique(),
            null_count=col_data.isna().sum(),
            sample_values=col_data.dropna().head(5).tolist(),
            statistics=statistics,
            is_key_field=col_data.nunique() > len(df) * 0.8,  # High uniqueness suggests key field
            recommended_role="measure" if data_type in [DataType.INTEGER, DataType.FLOAT] else "dimension"
        )
        columns.append(column_spec)
    
    # Calculate data quality score
    total_nulls = sum(col.null_count for col in columns)
    total_cells = len(df) * len(df.columns)
    data_quality_score = 1 - (total_nulls / total_cells) if total_cells > 0 else 0
    
    return DatasetSchema(
        name="uploaded_dataset",
        total_rows=len(df),
        total_columns=len(df.columns),
        columns=columns,
        data_quality_score=data_quality_score
    )