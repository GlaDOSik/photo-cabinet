# Metadata index
Photo Cabinet doesn't directly work with your photo collection. It must scan your collection first, discover your photos
and load metadata to internal database. This database of metadata is called index and is used for fast image filtering 
and quering. It also works as intermediate storage of your custom metadata changes. They can be commited back to photos but
by default, they only live in the index. When tag in photo is changed outside of Photo Cabinet, the index should be refreshed
to reflect the changes. The content may be out-of-sync otherwise.

That way, Photo Cabinet can support 2 main workflows:

1. Photo Cabinet as master of truth - metadata added or updated by PC are contained only in the index.
2. Photo file as master of truth - metadata added or updated by PC is commited to files (or XMP cards)

__Photo Cabinet never updates your photos directly or automatically. Commit process is entirely in your hands
and always create copies of photos. It is up to you to review validity and integrate copies back to the original collection.__

## Filtering metadata
In many cases, you don't need to load all metadata to index. The more tags you load, the larger index will be and slower
will be to query. For this reason, you can control what is loaded to index by allow/deny rules.