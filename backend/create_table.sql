CREATE TABLE IF NOT EXISTS papers (
	    doi TEXT PRIMARY KEY,
	    title TEXT NOT NULL,
	    url TEXT NOT NULL,
	    authors TEXT NOT NULL,
	    summary TEXT NOT NULL,
	    created_time TIMESTAMPTZ NOT NULL DEFAULT NOW(),
	    key_info JSON,
	    is_requested BOOLEAN NOT NULL DEFAULT FALSE,
	    journal VARCHAR(255) NOT NULL,
	    is_related BOOLEAN NOT NULL DEFAULT FALSE,
	    type VARCHAR(255) NOT NULL,
	    published_date DATE NOT NULL,
	    is_downloaded VARCHAR(255) NOT NULL DEFAULT 'undownloaded',
	    pdf_path TEXT,
	    is_uploaded BOOLEAN NOT NULL DEFAULT FALSE,
	    oss_url TEXT
	);

