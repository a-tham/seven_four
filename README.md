# Seven/Four: Music Genre Prediction and Audio Sample Recommendation

Please refer to the PDF slides (seven_four_capstone.pdf) for further details.

This is a project that helps musicians seeking to find audio samples via a song genre prediction.

Please check requirements.txt for the running of the main Jupyter notebook (seven_four.ipynb).

Please check requirements_working_file.txt for the running of the full project Jupyter notebook (seven_four_working_file.ipynb)

# Why Seven/Four?

Seven/Four (stylised as 7/4) is an uncommon and unique time signature notation that indicates having 7 beats in a bar, instead of the common 4/4 time signature.

# What does Seven/Four do?

Seven/Four is a music genre prediction & sample recommendation system.
 
Its aim is to provide musicians an all-in-one method to obtain royalty-free audio samples related to the genre of a track selected. The samples can then be used in a digital audio workstation.

Seven/Four checks what a user wants to listen to via the artist input, and then it will proceed to ask for album and track before hitting Spotify's API to
obtain the 30s preview URL.

The library module, Librosa, proceeds to convert these into Mel-spectrograms before running it through the Conv1D neural network.

The neural network currently runs 3 convolution layers and a dense layer to predict across 7 genres.

The genre will recommend 10 audio samples derived from Freesound's API, which is ready for downloading and usage.

I intend to deploy this project for usage to test out its function in public.
