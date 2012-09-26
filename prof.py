def main(mbid):

    # This is the main function for profiling
    # We've renamed our original main() above to real_main()
    import cProfile, pstats, StringIO
    prof = cProfile.Profile()
    prof = prof.runctx("real_main()", globals(), locals())
    stream = StringIO.StringIO()
    stats = pstats.Stats(prof, stream=stream)
    stats.sort_stats("cumulative")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    logging.info("Profile data:\n%s", stream.getvalue())

def real_main():
    mbid="6b966946-5274-4e3d-aabb-7563814d805f"
    artist=get_artist_mb(mbid)
    logging.error(artist)
        
    album_mbid=get_albums_mb(mbid)
    images=[]



    similar=get_similar(mbid)
    similar_mbid=[]
    for s in similar:
        logging.error(s)
        mbid=s[1]
        logo=get_image(mbid,s[0],'artist')
        logging.error(s[0])
        similar_mbid.append((mbid,logo))
            
                
    image=get_image(mbid,artist,'artist')
        
    bg=get_image(mbid,artist,'bg')
