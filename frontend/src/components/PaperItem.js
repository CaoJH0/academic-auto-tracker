import React from 'react';

const PaperItem = ({ paper }) => {
    return (
        <div className="col-lg-4 col-md-6 mb-4"> {/* 使用 Bootstrap 的列布局 */}
            <div className="card border-primary h-100 shadow"> {/* 卡片组件 */}
                <div className="card-body">
                    <h5 className="card-title">{paper.title}</h5>
                    <h6 className="card-subtitle mb-2 text-muted">{paper.authors}</h6>
                   
                    <p className="card-text">
                        <strong>Published Date:</strong> {paper.published_date}
                    </p>
                    <p className="card-text">
                        <strong>Journal:</strong> {paper.journal}
                    </p>
                    <p className="card-text">
                        <strong>Type:</strong> {paper.type}
                    </p>
                    <p className="card-text">
                        <strong>Related:</strong> {paper.is_related ? 'Yes' : 'No'}
                    </p>
                    <h6 className="mt-3">Key Information:</h6>
                    <ul className="list-unstyled">
                        <li>1. {paper.key_info.key_info_1}</li>
	                <li>2. {paper.key_info.key_info_2}</li>
	                <li>3. {paper.key_info.key_info_3}</li>
	                <li>4. {paper.key_info.key_info_4}</li>
                    </ul>
                </div>
                <div className="card-footer">
                    <a href={paper.url} className="btn btn-primary" target="_blank" rel="noopener noreferrer">View Article</a> {/* 添加链接按钮 */}
                </div>
            </div>
        </div>
        
    );
};

export default PaperItem;

