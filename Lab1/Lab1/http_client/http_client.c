/* The code is subject to Purdue University copyright policies.
 * Do not share, distribute, or post online.
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <fcntl.h>
#include <sys/stat.h>


int main(int argc, char *argv[])
{   
    int sockfd, numbytes;
	struct sockaddr_in their_addr;
	struct hostent* he;
    char response[1000];
    char status[1000];
    char request[1000];
	char *content;
    int content_len = -1;
    int remaining;
    char *filename = strrchr(argv[3],'/') + 1;
    FILE* file = NULL;

    if (argc != 4) {
        fprintf(stderr, "usage: ./http_client [host] [port number] [filepath]\n");
        exit(1);
    }

    if ((he = gethostbyname(argv[1])) == NULL) {
		herror("gethostbyname");
		exit(1);
	}

	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		perror("socket");
		exit(1);
	}

	their_addr.sin_family = AF_INET;
	their_addr.sin_port = htons(atoi(argv[2]));
	their_addr.sin_addr = *((struct in_addr *)he->h_addr_list[0]);
	bzero(&(their_addr.sin_zero), 8);

	if (connect(sockfd, (struct sockaddr *) &their_addr,
    sizeof(struct sockaddr)) < 0) {
		perror("connect");
		exit(1);
	}

	snprintf(request, sizeof(request), 
             "GET %s HTTP/1.0\r\n"
             "Host: %s:%s\r\n"
             "\r\n", 
             argv[3], argv[1], argv[2]);

	if (send(sockfd, request, strlen(request), 0) < 0) {
        perror("send");
        exit(1);
    }

	
	file = fopen(filename, "wb");
	if (file == NULL) {
            perror("Error opening file");
			close(sockfd);
            return 1;
    }
    if ((numbytes = recv(sockfd, response, sizeof(response) - 1,0)) > 0) {
        response[numbytes] = '\0'; 
        
    
        strncpy(status, response, sizeof(status) - 1);
        status[sizeof(status) - 1] = '\0';  

        //printf("Status Line: %s\n", status_line);

		if (strstr(status, "Content-Length:") != NULL) {
            content_len = atoi(strstr(status, "Content-Length:") + strlen("Content-Length:"));  
        }

		if (content_len == -1) {
        	fprintf(stderr, "Error: could not download the requested file (file length unknown)\n");
			fclose(file);
        	close(sockfd);
        	exit(1);
    	}
		remaining = content_len;

		char* tok = strtok(status, "\r\n");
		if (strstr(tok, "200") == NULL) {
        	printf("%s\r\n", tok);  
			fclose(file);
        	close(sockfd);
        	exit(1);
    	}

		content = strstr(response, "\r\n\r\n");
		if (content != NULL) {
        	content += 4; 
    	}
		if (content != NULL) {
        
       
		//printf("%s\n",content);
        while (*content != '\0') {
            fwrite(content, 1, 1, file);  
            content++;  
			remaining -= sizeof(char);
        }

		while (remaining > 0 && (numbytes = read(sockfd, response, sizeof(response))) > 0) {
        	fwrite(response, 1, numbytes, file);
        	remaining -= numbytes;
			//printf("here2\n");
    	}




    } 

    }


	fclose(file);
    close(sockfd);

    return 0;
}

