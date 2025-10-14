"""
AI Analysis Engine for Tableau Dashboard Generation.
Uses AzureOpenAI and Langchain for intelligent data analysis and dashboard recommendations.
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_openai import AzureChatOpenAI
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import BaseOutputParser
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..models.schemas import (
    DatasetSchema, AIAnalysisRequest, AIAnalysisResponse, 
    AIRecommendation, KPISpecification, VisualizationSpec,
    VisualizationType, ColorScheme, DataType
)
from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)

class DataInsights(BaseModel):
    """Structured data insights from AI analysis"""
    data_characteristics: Dict[str, Any] = Field(..., description="Key characteristics of the dataset")
    business_potential: List[str] = Field(..., description="Potential business insights")
    data_quality_issues: List[str] = Field(..., description="Identified data quality issues")
    recommended_preprocessing: List[str] = Field(..., description="Recommended data preprocessing steps")

class TableauDashboardAnalyzer:
    """
    Advanced AI analyzer for Tableau dashboard generation using meta-prompting techniques.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.llm = self._initialize_llm()
        self.data_analyzer_chain = self._create_data_analyzer_chain()
        self.dashboard_designer_chain = self._create_dashboard_designer_chain()
        self.kpi_generator_chain = self._create_kpi_generator_chain()
        self.visualization_recommender_chain = self._create_visualization_recommender_chain()
    
    def _initialize_llm(self) -> AzureChatOpenAI:
        """Initialize the Azure OpenAI language model"""
        try:
            return AzureChatOpenAI(
                azure_endpoint=self.config.azure_openai.endpoint,
                api_key=self.config.azure_openai.api_key,
                api_version=self.config.azure_openai.api_version,
                deployment_name=self.config.azure_openai.deployment_name,
                model_name=self.config.azure_openai.model_name,
                temperature=self.config.azure_openai.temperature,
                max_tokens=self.config.azure_openai.max_tokens,
                top_p=self.config.azure_openai.top_p
            )
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI: {e}")
            raise
    
    def _create_data_analyzer_chain(self):
        """Create the data analysis chain with meta-prompting"""
        system_prompt = SystemMessagePromptTemplate.from_template(
            self.config.meta_prompting.system_prompts.data_analyzer + 
            """
            
            CRITICAL INSTRUCTIONS:
            1. Analyze the dataset schema and provide structured insights
            2. Focus on business relevance and dashboard potential
            3. Identify key metrics, dimensions, and relationships
            4. Consider data quality and preprocessing needs
            5. Provide actionable recommendations
            
            Response must be a valid JSON object with these keys:
            - data_characteristics: Object with key dataset properties
            - business_potential: Array of potential business insights
            - data_quality_issues: Array of identified issues
            - recommended_preprocessing: Array of preprocessing suggestions
            """
        )
        
        human_prompt = HumanMessagePromptTemplate.from_template(
            """
            Analyze this dataset schema for Tableau dashboard creation:
            
            Dataset: {dataset_name}
            Rows: {total_rows}
            Columns: {total_columns}
            Data Quality Score: {data_quality_score}
            
            Column Details:
            {column_details}
            
            Business Context: {business_context}
            Business Goals: {business_goals}
            Target Audience: {target_audience}
            
            Provide comprehensive analysis as requested.
            """
        )
        
        prompt_template = ChatPromptTemplate.from_messages([system_prompt, human_prompt])
        
        class DataInsightsOutputParser(BaseOutputParser[DataInsights]):
            def parse(self, text: str) -> DataInsights:
                try:
                    # Clean the response to extract JSON
                    cleaned_text = text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:-3]
                    elif cleaned_text.startswith("```"):
                        cleaned_text = cleaned_text[3:-3]
                    
                    data = json.loads(cleaned_text)
                    return DataInsights(**data)
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse AI response as JSON: {e}")
                    # Fallback parsing
                    return DataInsights(
                        data_characteristics={"parsed_error": str(e)},
                        business_potential=["Unable to parse AI response"],
                        data_quality_issues=["Response parsing failed"],
                        recommended_preprocessing=["Review AI response format"]
                    )
        
        return prompt_template | self.llm | DataInsightsOutputParser()
    
    def _create_dashboard_designer_chain(self):
        """Create dashboard design recommendation chain"""
        system_prompt = SystemMessagePromptTemplate.from_template(
            self.config.meta_prompting.system_prompts.dashboard_designer + 
            """
            
            CRITICAL INSTRUCTIONS:
            1. Design optimal dashboard layouts based on data analysis
            2. Consider user experience and business goals
            3. Recommend color schemes and visual hierarchy
            4. Focus on performance and usability
            5. Provide reasoning for all recommendations
            
            Response format (JSON):
            {
              "layout_recommendation": {
                "confidence_score": 0.85,
                "reasoning": "Explanation of layout choice",
                "alternatives": ["Alternative 1", "Alternative 2"]
              },
              "color_scheme_recommendation": {
                "confidence_score": 0.90,
                "reasoning": "Color scheme rationale", 
                "alternatives": ["tableau20", "category10"]
              },
              "performance_considerations": ["Consideration 1", "Consideration 2"]
            }
            """
        )
        
        human_prompt = HumanMessagePromptTemplate.from_template(
            """
            Design dashboard layout based on:
            
            Data Insights: {data_insights}
            Business Goals: {business_goals}
            Target Audience: {target_audience}
            Dataset Schema: {dataset_info}
            
            Provide structured design recommendations.
            """
        )
        
        return ChatPromptTemplate.from_messages([system_prompt, human_prompt]) | self.llm
    
    def _create_kpi_generator_chain(self):
        """Create KPI generation chain"""
        system_prompt = SystemMessagePromptTemplate.from_template(
            self.config.meta_prompting.system_prompts.worksheet_creator + 
            """
            
            CRITICAL INSTRUCTIONS:
            1. Generate relevant KPIs based on data analysis
            2. Create Tableau-compatible calculations
            3. Prioritize KPIs by business importance
            4. Include proper formatting specifications
            5. Ensure calculations are syntactically correct for Tableau
            
            Response format (JSON Array):
            [
              {
                "name": "KPI Name",
                "description": "KPI Description",
                "calculation": "Tableau calculation formula",
                "target_value": 100.0,
                "format_string": "#,##0.0%",
                "priority": 1
              }
            ]
            """
        )
        
        human_prompt = HumanMessagePromptTemplate.from_template(
            """
            Generate KPIs for this dataset:
            
            Data Analysis: {data_insights}
            Column Details: {column_details}
            Business Goals: {business_goals}
            
            Create 3-7 relevant KPIs with proper Tableau calculations.
            """
        )
        
        return ChatPromptTemplate.from_messages([system_prompt, human_prompt]) | self.llm
    
    def _create_visualization_recommender_chain(self):
        """Create visualization recommendation chain"""
        system_prompt = SystemMessagePromptTemplate.from_template(
            """
            You are an expert Tableau visualization specialist. Recommend specific visualizations 
            based on data characteristics and business goals.
            
            CRITICAL INSTRUCTIONS:
            1. Recommend appropriate chart types for each data relationship
            2. Specify exact field mappings (x-axis, y-axis, color, size)
            3. Consider data types and cardinality
            4. Optimize for user understanding and insight discovery
            5. Ensure visualizations work well together in a dashboard
            
            Response format (JSON Array):
            [
              {
                "chart_type": "bar",
                "title": "Chart Title",
                "x_axis": ["field1"],
                "y_axis": ["field2"],
                "color_field": "field3",
                "size_field": null,
                "filters": [],
                "color_scheme": "tableau10",
                "show_labels": true,
                "show_legend": true,
                "aggregation_type": "sum"
              }
            ]
            """
        )
        
        human_prompt = HumanMessagePromptTemplate.from_template(
            """
            Recommend visualizations for:
            
            Dataset Schema: {dataset_schema}
            Business Goals: {business_goals}
            Data Insights: {data_insights}
            KPIs: {kpis}
            
            Create 4-8 complementary visualizations that tell a cohesive story.
            """
        )
        
        return ChatPromptTemplate.from_messages([system_prompt, human_prompt]) | self.llm
    
    async def analyze_dataset(self, request: AIAnalysisRequest) -> AIAnalysisResponse:
        """
        Perform comprehensive AI analysis of the dataset for dashboard generation.
        """
        try:
            logger.info(f"Starting AI analysis for dataset: {request.dataset_schema.name}")
            
            # Prepare data for analysis
            column_details = self._format_column_details(request.dataset_schema.columns)
            
            # Step 1: Data Analysis
            logger.info("Performing data analysis...")
            data_insights = await self._run_data_analysis(
                request.dataset_schema, column_details, request.business_goals, 
                request.target_audience
            )
            
            # Step 2: Dashboard Design Recommendations
            logger.info("Generating dashboard design recommendations...")
            design_recommendations = await self._run_dashboard_design(
                data_insights, request.business_goals, request.target_audience,
                request.dataset_schema
            )
            
            # Step 3: KPI Generation
            logger.info("Generating KPI recommendations...")
            kpis = await self._run_kpi_generation(
                data_insights, column_details, request.business_goals
            )
            
            # Step 4: Visualization Recommendations
            logger.info("Generating visualization recommendations...")
            visualizations = await self._run_visualization_recommendations(
                request.dataset_schema, request.business_goals, data_insights, kpis
            )
            
            # Parse design recommendations
            layout_rec, color_rec, performance_considerations = self._parse_design_recommendations(
                design_recommendations
            )
            
            # Create final response
            response = AIAnalysisResponse(
                dataset_insights=data_insights.dict(),
                recommended_kpis=kpis,
                recommended_visualizations=visualizations,
                dashboard_recommendations=layout_rec,
                layout_suggestions=layout_rec,  # Same as dashboard for now
                color_scheme_recommendation=color_rec,
                performance_considerations=performance_considerations
            )
            
            logger.info("AI analysis completed successfully")
            return response
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise
    
    def _format_column_details(self, columns) -> str:
        """Format column details for AI analysis"""
        details = []
        for col in columns:
            stats_str = ""
            if col.statistics:
                stats_str = f" (mean: {col.statistics.get('mean', 'N/A')}, std: {col.statistics.get('std', 'N/A')})"
            
            details.append(
                f"- {col.name}: {col.data_type.value}, "
                f"{col.unique_values} unique values, "
                f"{col.null_count} nulls{stats_str}"
            )
        return "\n".join(details)
    
    async def _run_data_analysis(self, schema, column_details, business_goals, target_audience) -> DataInsights:
        """Run the data analysis chain"""
        try:
            result = await self.data_analyzer_chain.ainvoke({
                "dataset_name": schema.name,
                "total_rows": schema.total_rows,
                "total_columns": schema.total_columns,
                "data_quality_score": schema.data_quality_score,
                "column_details": column_details,
                "business_context": schema.business_context or "General business analysis",
                "business_goals": ", ".join(business_goals),
                "target_audience": target_audience
            })
            return result
        except Exception as e:
            logger.warning(f"Data analysis chain failed: {e}")
            # Fallback
            return DataInsights(
                data_characteristics={"total_rows": schema.total_rows, "total_columns": schema.total_columns},
                business_potential=["Analyze key metrics and trends"],
                data_quality_issues=["No specific issues identified"],
                recommended_preprocessing=["Standard data cleaning"]
            )
    
    async def _run_dashboard_design(self, data_insights, business_goals, target_audience, dataset_schema):
        """Run dashboard design recommendation"""
        try:
            result = await self.dashboard_designer_chain.ainvoke({
                "data_insights": json.dumps(data_insights.dict(), indent=2),
                "business_goals": ", ".join(business_goals),
                "target_audience": target_audience,
                "dataset_info": f"Rows: {dataset_schema.total_rows}, Columns: {dataset_schema.total_columns}"
            })
            return result.content
        except Exception as e:
            logger.warning(f"Dashboard design chain failed: {e}")
            return json.dumps({
                "layout_recommendation": {
                    "confidence_score": 0.5,
                    "reasoning": "Default grid layout recommended",
                    "alternatives": ["automatic", "free_form"]
                },
                "color_scheme_recommendation": {
                    "confidence_score": 0.7,
                    "reasoning": "Tableau10 provides good color differentiation",
                    "alternatives": ["tableau20", "category10"]
                },
                "performance_considerations": ["Limit number of marks", "Use appropriate aggregation"]
            })
    
    async def _run_kpi_generation(self, data_insights, column_details, business_goals) -> List[KPISpecification]:
        """Generate KPI recommendations"""
        try:
            result = await self.kpi_generator_chain.ainvoke({
                "data_insights": json.dumps(data_insights.dict(), indent=2),
                "column_details": column_details,
                "business_goals": ", ".join(business_goals)
            })
            
            kpi_data = json.loads(result.content)
            return [KPISpecification(**kpi) for kpi in kpi_data]
        except Exception as e:
            logger.warning(f"KPI generation failed: {e}")
            # Return default KPIs
            return [
                KPISpecification(
                    name="Record Count",
                    description="Total number of records",
                    calculation="COUNTD([Record Number])",
                    format_string="#,##0",
                    priority=1
                )
            ]
    
    async def _run_visualization_recommendations(self, schema, business_goals, data_insights, kpis) -> List[VisualizationSpec]:
        """Generate visualization recommendations"""
        try:
            result = await self.visualization_recommender_chain.ainvoke({
                "dataset_schema": json.dumps({
                    "columns": [col.dict() for col in schema.columns],
                    "total_rows": schema.total_rows
                }, indent=2),
                "business_goals": ", ".join(business_goals),
                "data_insights": json.dumps(data_insights.dict(), indent=2),
                "kpis": json.dumps([kpi.dict() for kpi in kpis], indent=2)
            })
            
            viz_data = json.loads(result.content)
            return [VisualizationSpec(**viz) for viz in viz_data]
        except Exception as e:
            logger.warning(f"Visualization recommendation failed: {e}")
            # Return default visualizations based on column types
            return self._generate_default_visualizations(schema)
    
    def _generate_default_visualizations(self, schema) -> List[VisualizationSpec]:
        """Generate default visualizations based on data types"""
        visualizations = []
        numeric_cols = [col for col in schema.columns if col.data_type in [DataType.INTEGER, DataType.FLOAT]]
        categorical_cols = [col for col in schema.columns if col.data_type == DataType.CATEGORICAL]
        
        if numeric_cols and categorical_cols:
            visualizations.append(
                VisualizationSpec(
                    chart_type=VisualizationType.BAR,
                    title=f"{numeric_cols[0].name} by {categorical_cols[0].name}",
                    x_axis=[categorical_cols[0].name],
                    y_axis=[numeric_cols[0].name],
                    aggregation_type="sum"
                )
            )
        
        if len(numeric_cols) >= 2:
            visualizations.append(
                VisualizationSpec(
                    chart_type=VisualizationType.SCATTER,
                    title=f"{numeric_cols[0].name} vs {numeric_cols[1].name}",
                    x_axis=[numeric_cols[0].name],
                    y_axis=[numeric_cols[1].name],
                    aggregation_type="avg"
                )
            )
        
        return visualizations
    
    def _parse_design_recommendations(self, design_rec_str):
        """Parse design recommendations from AI response"""
        try:
            data = json.loads(design_rec_str)
            
            layout_rec = AIRecommendation(
                confidence_score=data.get("layout_recommendation", {}).get("confidence_score", 0.5),
                reasoning=data.get("layout_recommendation", {}).get("reasoning", "Default layout"),
                alternatives=data.get("layout_recommendation", {}).get("alternatives", [])
            )
            
            color_rec = AIRecommendation(
                confidence_score=data.get("color_scheme_recommendation", {}).get("confidence_score", 0.7),
                reasoning=data.get("color_scheme_recommendation", {}).get("reasoning", "Default colors"),
                alternatives=data.get("color_scheme_recommendation", {}).get("alternatives", [])
            )
            
            performance_considerations = data.get("performance_considerations", [])
            
            return layout_rec, color_rec, performance_considerations
            
        except Exception as e:
            logger.warning(f"Failed to parse design recommendations: {e}")
            return (
                AIRecommendation(confidence_score=0.5, reasoning="Default recommendation", alternatives=[]),
                AIRecommendation(confidence_score=0.7, reasoning="Default color scheme", alternatives=[]),
                ["Use appropriate aggregation", "Limit data points"]
            )