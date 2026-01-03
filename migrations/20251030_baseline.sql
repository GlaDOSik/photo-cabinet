-- public.app_data definition

-- Drop table

-- DROP TABLE public.app_data;

CREATE TABLE public.app_data (
	id uuid NOT NULL,
	field_name varchar NOT NULL,
	field_value varchar NULL,
	CONSTRAINT app_data_pkey PRIMARY KEY (id)
);


-- public.exif_group definition

-- Drop table

-- DROP TABLE public.exif_group;

CREATE TABLE public.exif_group (
	id uuid NOT NULL,
	"namespace" varchar NOT NULL,
	g0 varchar NOT NULL,
	g1 varchar NOT NULL,
	g2 varchar NOT NULL,
	user_created bool NOT NULL,
	deleted bool NOT NULL,
	CONSTRAINT exif_group_pkey PRIMARY KEY (id)
);


-- public.metadata_indexing_group definition

-- Drop table

-- DROP TABLE public.metadata_indexing_group;

CREATE TABLE public.metadata_indexing_group (
	id uuid NOT NULL,
	created timestamp NOT NULL,
	group_name varchar NOT NULL,
	"type" varchar(5) NOT NULL,
	file_path_match varchar NULL,
	CONSTRAINT metadata_indexing_group_pkey PRIMARY KEY (id)
);

-- public.task definition

-- Drop table

-- DROP TABLE public.task;

CREATE TABLE public.task (
	id uuid NOT NULL,
	"name" varchar NULL,
	"type" varchar(17) NOT NULL,
	status varchar(11) NOT NULL,
	progress_max int4 NULL,
	progress_current int4 NULL,
	"start" timestamp NULL,
	"end" timestamp NULL,
	error_msg varchar NULL,
	CONSTRAINT task_pkey PRIMARY KEY (id)
);


-- public.exif_tag definition

-- Drop table

-- DROP TABLE public.exif_tag;

CREATE TABLE public.exif_tag (
	id uuid NOT NULL,
	group_id uuid NOT NULL,
	exif_id varchar NOT NULL,
	"name" varchar NOT NULL,
	"type" varchar NOT NULL,
	description varchar NOT NULL,
	writable bool NOT NULL,
	is_list bool NOT NULL,
	field_name varchar NULL,
	parent_struct_id uuid NULL,
	user_created bool NOT NULL,
	deleted bool NOT NULL,
	CONSTRAINT exif_tag_pkey PRIMARY KEY (id),
	CONSTRAINT exif_tag_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.exif_group(id),
	CONSTRAINT exif_tag_parent_struct_id_fkey FOREIGN KEY (parent_struct_id) REFERENCES public.exif_tag(id)
);


-- public.exif_value definition

-- Drop table

-- DROP TABLE public.exif_value;

CREATE TABLE public.exif_value (
	id uuid NOT NULL,
	tag_id uuid NOT NULL,
	value varchar NOT NULL,
	user_created bool NOT NULL,
	deleted bool NOT NULL,
	CONSTRAINT exif_value_pkey PRIMARY KEY (id),
	CONSTRAINT exif_value_tag_id_fkey FOREIGN KEY (tag_id) REFERENCES public.exif_tag(id)
);


-- public.folder definition

-- Drop table

-- DROP TABLE public.folder;

CREATE TABLE public.folder (
	id uuid NOT NULL,
	parent_id uuid NULL,
	"name" varchar NOT NULL,
	CONSTRAINT folder_pkey PRIMARY KEY (id),
	CONSTRAINT folder_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.folder(id) ON DELETE CASCADE
);


-- public.metadata_indexing_filter definition

-- Drop table

-- DROP TABLE public.metadata_indexing_filter;

CREATE TABLE public.metadata_indexing_filter (
	id uuid NOT NULL,
	group_id uuid NOT NULL,
	g0 varchar NULL,
	g1 varchar NULL,
	tag_name varchar NULL,
	CONSTRAINT metadata_indexing_filter_pkey PRIMARY KEY (id),
	CONSTRAINT metadata_indexing_filter_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.metadata_indexing_group(id) ON DELETE CASCADE
);


-- public.photo definition

-- Drop table

-- DROP TABLE public.photo;

CREATE TABLE public.photo (
	id uuid NOT NULL,
	folder_id uuid NOT NULL,
	file_path varchar NOT NULL,
	file_hash varchar NOT NULL,
	"name" varchar NOT NULL,
	created timestamp NULL,
	CONSTRAINT photo_pkey PRIMARY KEY (id),
	CONSTRAINT photo_folder_id_fkey FOREIGN KEY (folder_id) REFERENCES public.folder(id) ON DELETE CASCADE
);


-- public.photo_metadata definition

-- Drop table

-- DROP TABLE public.photo_metadata;

CREATE TABLE public.photo_metadata (
	id uuid NOT NULL,
	photo_id uuid NOT NULL,
	exif_json jsonb NOT NULL,
	user_json jsonb NULL,
	effective_json jsonb NULL,
	CONSTRAINT photo_metadata_pkey PRIMARY KEY (id),
	CONSTRAINT photo_metadata_photo_id_fkey FOREIGN KEY (photo_id) REFERENCES public.photo(id) ON DELETE CASCADE
);


-- public.task_log definition

-- Drop table

-- DROP TABLE public.task_log;

CREATE TABLE public.task_log (
	id uuid NOT NULL,
	task_id uuid NOT NULL,
	"timestamp" timestamp NOT NULL,
	severity varchar(7) NOT NULL,
	message varchar NOT NULL,
	CONSTRAINT task_log_pkey PRIMARY KEY (id),
	CONSTRAINT task_log_task_id_fkey FOREIGN KEY (task_id) REFERENCES public.task(id)
);


-- Create default root folders
INSERT INTO public.folder
(id, parent_id, "name")
VALUES('1587573f-2748-4562-8ffe-4b96506302da'::uuid, NULL, 'ROOT');
INSERT INTO public.folder
(id, parent_id, "name")
VALUES('177f99c4-84c8-4005-9103-ebde67fed9e4'::uuid, NULL, 'LIMBO');