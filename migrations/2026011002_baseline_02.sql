-- Create default root folders
INSERT INTO public.folder
(id, parent_id, "name", folder_type)
VALUES('1587573f-2748-4562-8ffe-4b96506302da'::uuid, NULL, 'ROOT', 'COLLECTION');
INSERT INTO public.folder
(id, parent_id, "name", folder_type)
VALUES('177f99c4-84c8-4005-9103-ebde67fed9e4'::uuid, NULL, 'ROOT', 'LIMBO');
INSERT INTO public.folder
(id, parent_id, "name", folder_type)
VALUES('0914d89e-deb7-4107-9557-76d50236f0ab'::uuid, NULL, 'ROOT', 'VIRTUAL');