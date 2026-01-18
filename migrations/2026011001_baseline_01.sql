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
	file_path_match varchar NULL,
	group_type varchar(18) NOT NULL,
	filter_type varchar(5) NULL,
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
	folder_type varchar(10) NOT NULL,
	CONSTRAINT folder_pkey PRIMARY KEY (id),
	CONSTRAINT folder_parent_id_fkey FOREIGN KEY (parent_id) REFERENCES public.folder(id) ON DELETE CASCADE
);


-- public.metadata_indexing_tag definition

-- Drop table

-- DROP TABLE public.metadata_indexing_tag;

CREATE TABLE public.metadata_indexing_tag (
	id uuid NOT NULL,
	group_id uuid NOT NULL,
	"order" int4 NOT NULL,
	g0 varchar NULL,
	g1 varchar NULL,
	tag_name varchar NULL,
	tag_path varchar NULL,
	CONSTRAINT metadata_indexing_tag_pkey PRIMARY KEY (id),
	CONSTRAINT metadata_indexing_tag_group_id_fkey FOREIGN KEY (group_id) REFERENCES public.metadata_indexing_group(id) ON DELETE CASCADE
);


-- public.photo definition

-- Drop table

-- DROP TABLE public.photo;

CREATE TABLE public.photo (
	id uuid NOT NULL,
	folder_id uuid NOT NULL,
	virtual_folder_id uuid NOT NULL,
	file_path varchar NOT NULL,
	file_hash varchar NOT NULL,
	"name" varchar NOT NULL,
	CONSTRAINT photo_pkey PRIMARY KEY (id),
	CONSTRAINT photo_folder_id_fkey FOREIGN KEY (folder_id) REFERENCES public.folder(id),
	CONSTRAINT photo_virtual_folder_id_fkey FOREIGN KEY (virtual_folder_id) REFERENCES public.folder(id)
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
	photo_created timestamp NULL,
	photo_created_origin varchar NULL,
	width int4 NULL,
	height int4 NULL,
	size_origin varchar NULL,
	use_thumbnail bool NOT NULL,
	preview_color_hex varchar NULL,
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