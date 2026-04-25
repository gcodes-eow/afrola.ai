# ai_engine/tasks.py - Add:

@shared_task
def create_dubbed_audio_task(job_id, voice_id):
    """Generate dubbed audio from translated text"""
    job = Job.objects.get(id=job_id)
    voice = VoiceModel.objects.get(id=voice_id)
    
    # Synthesize speech
    audio_path = synthesize_speech(
        text=job.translation,
        voice=voice,
        output_format='mp3'
    )
    
    job.audio_output = audio_path
    job.save()
    return audio_path

@shared_task
def create_dubbed_video_task(job_id, voice_id, options):
    """Replace audio track in video with dubbed version"""
    job = Job.objects.get(id=job_id)
    
    # Extract original video metadata
    video_info = get_video_metadata(job.source_file.path)
    
    # Generate dubbed audio
    dubbed_audio = create_dubbed_audio_task(job_id, voice_id)
    
    # Merge audio with video
    output_path = merge_audio_video(
        video_path=job.source_file.path,
        audio_path=dubbed_audio,
        output_format='mp4'
    )
    
    job.output_video = output_path
    job.status = 'completed'
    job.save()