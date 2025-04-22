#!/usr/bin/env python3

import os
import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from jinja2 import Environment, FileSystemLoader

def create_score_distribution_plot(predictions):
    """Create score distribution visualization"""
    scores = [p['score'] for p in predictions]
    fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=20)])
    fig.update_layout(
        title="Distribution of Prediction Scores",
        xaxis_title="Score",
        yaxis_title="Count"
    )
    return fig.to_html(full_html=False)

def create_property_scatter_plot(predictions):
    """Create molecular property scatter plot"""
    data = []
    for p in predictions:
        props = p['molecular_properties']
        data.append({
            'id': p['compound_id'],
            'score': p['score'],
            'MW': props['MW'],
            'LogP': props['LogP'],
            'TPSA': props['TPSA']
        })
    
    df = pd.DataFrame(data)
    fig = px.scatter_3d(df, x='MW', y='LogP', z='TPSA',
                       color='score', hover_data=['id'])
    fig.update_layout(title="Molecular Property Space")
    return fig.to_html(full_html=False)

def create_validation_summary(validation_results):
    """Create validation summary tables"""
    summary = {
        'total_compounds': validation_results['total_compounds'],
        'compounds_above_threshold': validation_results['compounds_above_threshold'],
        'average_score': f"{validation_results['average_score']:.3f}",
        'pass_rates': {
            'MW_CHECK': 0,
            'LOGP_CHECK': 0,
            'HBA_CHECK': 0,
            'HBD_CHECK': 0
        }
    }
    
    # Calculate pass rates for each check
    for compound in validation_results['validation_checks']:
        for check_name, passed, _ in compound['checks']:
            if passed:
                summary['pass_rates'][check_name] = summary['pass_rates'].get(check_name, 0) + 1
    
    # Convert to percentages
    total = validation_results['total_compounds']
    for check in summary['pass_rates']:
        summary['pass_rates'][check] = f"{(summary['pass_rates'][check] / total * 100):.1f}%"
    
    return summary

def generate_report(input_file, output_dir):
    # Load validated results
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    predictions = data['predictions']
    validation_results = data['validation_results']
    blockchain_data = data['blockchain_data']
    
    # Create visualizations
    score_plot = create_score_distribution_plot(predictions)
    property_plot = create_property_scatter_plot(predictions)
    validation_summary = create_validation_summary(validation_results)
    
    # Prepare top compounds table
    top_compounds = []
    for pred in sorted(predictions, key=lambda x: x['score'], reverse=True)[:10]:
        props = pred['molecular_properties']
        top_compounds.append({
            'id': pred['compound_id'],
            'score': f"{pred['score']:.3f}",
            'MW': f"{props['MW']:.1f}",
            'LogP': f"{props['LogP']:.1f}",
            'TPSA': f"{props['TPSA']:.1f}",
            'HBA': props['HBA'],
            'HBD': props['HBD']
        })
    
    # Load and render template
    env = Environment(loader=FileSystemLoader('/app/templates'))
    template = env.get_template('report_template.html')
    
    report_html = template.render(
        timestamp=blockchain_data['timestamp'],
        model_type=blockchain_data['model_type'],
        confidence_threshold=blockchain_data['confidence_threshold'],
        validation_summary=validation_summary,
        top_compounds=top_compounds,
        score_plot=score_plot,
        property_plot=property_plot,
        blockchain_hash=blockchain_data['predictions_hash'],
        ipfs_hash=blockchain_data['ipfs_hash']
    )
    
    # Save report
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'report.html')
    with open(output_file, 'w') as f:
        f.write(report_html)
    
    return output_file

def main(input_file, output_dir):
    return generate_report(input_file, output_dir)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_file', required=True)
    parser.add_argument('--output_dir', required=True)
    
    args = parser.parse_args()
    main(args.input_file, args.output_dir) 