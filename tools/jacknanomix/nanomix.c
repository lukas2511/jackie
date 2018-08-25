#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <unistd.h>
#include <signal.h>

#include <jack/jack.h>
#include <getopt.h>
#include "config.h"

#define		DEFAULT_CLIENT_NAME		"nanomixer"		// Default name of JACK client

float current_gain;
jack_port_t *left_port;
jack_port_t *right_port;

jack_port_t *outport[2] = {NULL, NULL};
jack_client_t *client = NULL;

unsigned int running = 1;

static
void signal_handler (int signum)
{
	running = 0;
	close(0);
}


static
void shutdown_callback_jack(void *arg)
{
	running = 0;
	close(0);
}


static
int process_jack_audio(jack_nframes_t nframes, void *arg)
{
	jack_default_audio_sample_t *out_left = jack_port_get_buffer(outport[0], nframes);
	jack_default_audio_sample_t *out_right = jack_port_get_buffer(outport[1], nframes);
	
	jack_default_audio_sample_t *in_left = jack_port_get_buffer(left_port, nframes);
	jack_default_audio_sample_t *in_right = jack_port_get_buffer(right_port, nframes);

	for (jack_nframes_t n=0; n<nframes; n++ ) {
		out_left[n] = in_left[n] * current_gain;
		out_right[n] = in_right[n] * current_gain;
	}

	return 0;
}

static
void init_jack( const char * client_name ) 
{
	jack_status_t status;

	// Register with Jack
	if ((client = jack_client_open(client_name, JackNullOption, &status)) == 0) {
		fprintf(stderr, "Failed to start jack client: %d\n", status);
		exit(1);
	}
	printf("JACK client registered as '%s'.\n", jack_get_client_name( client ) );

	// Create our pair of output ports
	if (!(outport[0] = jack_port_register(client, "out_left", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0))) {
		fprintf(stderr, "Cannot register output port 'out_left'.\n");
		exit(1);
	}
	
	if (!(outport[1] = jack_port_register(client, "out_right", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0))) {
		fprintf(stderr, "Cannot register output port 'out_right'.\n");
		exit(1);
	}
	
	// Register shutdown callback
	jack_on_shutdown (client, shutdown_callback_jack, NULL );

	// Register the peak audio callback
	jack_set_process_callback(client, process_jack_audio, 0);
}

static
void finish_jack( jack_client_t *client )
{
	// Leave the Jack graph
	jack_client_close(client);
}

static
jack_port_t* create_input_port( const char* side )
{
	int port_name_size = jack_port_name_size();
	char *port_name = malloc( port_name_size );
	jack_port_t *port;
	
	snprintf( port_name, port_name_size, "in_%s", side );
	port = jack_port_register(client, port_name, JACK_DEFAULT_AUDIO_TYPE, JackPortIsInput, 0);
	if (!port) {
		fprintf(stderr, "Cannot register input port '%s'.\n", port_name);
		exit(1);
	}
	
	return port;
}

/* Display how to use this program */
static
int usage( )
{
	printf("JackMiniMix version %s\n\n", PACKAGE_VERSION);
	printf("Usage: %s [options]\n", PACKAGE_NAME);
	printf("   -n <name>     Name for this JACK client (default nanomix)\n");
	printf("\n");
	exit(1);
}


int main(int argc, char *argv[])
{
	char *client_name = DEFAULT_CLIENT_NAME;
	int opt;
	
	
	// Parse the command line arguments
	while ((opt = getopt(argc, argv, "n:h")) != -1) {
		switch (opt) {
			case 'n':  client_name = optarg; break;
			default:
				fprintf(stderr, "Unknown option '%c'.\n", (char)opt);
			case 'h':
				usage( argv[0] );
				break;
		}
	}
    argc -= optind;
    argv += optind;
	
	// Dislay welcoming message
	printf("Starting JackNanoMix version %s.\n", VERSION);

	// Set signal handlers
	signal(SIGTERM, signal_handler);
	signal(SIGINT, signal_handler);


	// Setup JACK
	init_jack(client_name);

	// Create the channel descriptors
	current_gain=0.0f;
	left_port = create_input_port("left");
	right_port = create_input_port("right");

	// Set JACK running
	if (jack_activate(client)) {
		fprintf(stderr, "Cannot activate client.\n");
		exit(1);
	}
	fflush(stdout);
	fflush(stderr);

	// Sleep until we are done (work is done in threads)
	while (running) {
		scanf("%f", &current_gain);
		//printf("New gain for %s: %.2f\n", client_name, current_gain);
	}

  // Cleanup
	finish_jack( client );

	return 0;
}

