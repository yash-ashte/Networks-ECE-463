/* The code is subject to Purdue University copyright policies.
 * Do not share, distribute, or post online.
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <netdb.h>
#include <arpa/inet.h>

#define LISTEN_QUEUE 50 /* Max outstanding connection requests; listen() param */

#define DBADDR "127.0.0.1"

#define MAX_BUFFER_SIZE 1000

void send_response_header(int client_fd, const char *status, size_t content_length) {
    char header[MAX_BUFFER_SIZE];
    snprintf(header, sizeof(header),
             "HTTP/1.0 %s\r\n"
             "Content-Length: %zu\r\n"
             "\r\n",
             status, content_length);
    int n = write(client_fd, header, strlen(header));
}




int main(int argc, char *argv[])
{   
    int n;

    if (argc != 3) {
        fprintf(stderr, "usage: ./http_server [server port] [DB port]\n");
        exit(1);
    }

    int sockfd, new_fd;
	struct sockaddr_in my_addr;
	struct sockaddr_in their_addr; /* client's address info */
	int sin_size;
	char dst[INET_ADDRSTRLEN];
    int servport = atoi(argv[1]);
    int dbport = atoi(argv[2]);

	if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
		perror("socket");
		exit(1);
	}

    my_addr.sin_family = AF_INET;
	my_addr.sin_port = htons(servport);
	my_addr.sin_addr.s_addr = INADDR_ANY; /* bind to all local interfaces */
	bzero(&(my_addr.sin_zero), 8);

    if (bind(sockfd, (struct sockaddr *) &my_addr, sizeof(struct sockaddr)) < 0) {
		perror("bind");
		exit(1);
	}

    if (listen(sockfd, LISTEN_QUEUE) < 0) {
		perror("listen");
		exit(1);
	}

    while(1) {
		sin_size = sizeof(struct sockaddr_in);
		if ((new_fd = accept(sockfd,
        (struct sockaddr *) &their_addr, &sin_size)) < 0) {
			perror("accept");
			continue;
		}

		//inet_ntop(AF_INET, &(their_addr.sin_addr), dst, INET_ADDRSTRLEN);
		//printf("server: got connection from %s\n", dst);\

       

        char req[MAX_BUFFER_SIZE];
        ssize_t bytes_received = recv(new_fd, req, sizeof(req) - 1, 0);
        if (bytes_received < 0) {
            perror("recv");
            close(new_fd);
            continue;
        }
        req[bytes_received] = '\0';  // Null-terminate the req
       // printf("req");
        // Parse the request line
        char method[16], uri[256], version[16], og[256];// code[256];
        sscanf(req, "%s %s %s", method, uri, version);
        sscanf(uri, "%s",og );

        // Log the request
        //printf("%s \"%s %s %s\"\n", inet_ntoa((&their_addr)->sin_addr), method, uri, version);

        if (strcmp(method, "GET") != 0) {
            send_response_header(new_fd, "501 Not Implemented", 0);
            n = write(new_fd, "<html><body><h1>501 Not Implemented</h1></body></html>", strlen("<html><body><h1>501 Not Implemented</h1></body></html>"));
            printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "501 Not Implemented");
            close(new_fd);
            continue;
        }

        if (strcmp(version, "HTTP/1.0") != 0 && strcmp(version, "HTTP/1.1") != 0 ) {
            send_response_header(new_fd, "501 Not Implemented", 0);
            n = write(new_fd, "<html><body><h1>501 Not Implemented</h1></body></html>", strlen("<html><body><h1>501 Not Implemented</h1></body></html>"));
            printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "501 Not Implemented");
            close(new_fd);
            continue;
        }

        

        // Validate the URI format
        if (uri[0] != '/' || strstr(uri, "/../") != NULL ||(uri[strlen(uri)-3] == '/' && uri[strlen(uri)-2] == '.' && uri[strlen(uri)-1] == '.')) {
            //printf("%s\n", uri);
            send_response_header(new_fd, "400 Bad Request",  0);
            n = write(new_fd, "<html><body><h1>400 Bad Request</h1></body></html>", strlen("<html><body><h1>400 Bad Request</h1></body></html>"));
            printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "400 Bad Request");
            
            close(new_fd);
            continue;
        }

        // If URI ends with '/', serve index.html
        //int con = 0;
        if (uri[strlen(uri) - 1] == '/') {
            strncat(uri, "index.html", sizeof(uri) - strlen(uri) - 1);
            //con = 1;
        }



        //DATA BASE SERVER (PART 2)

        if (strstr(uri, "?key="))
        {
            
            //printf("here-key\n");
            char* query = strstr(uri, "?key=") + 5;

            //printf("%s\n", query);
            for (int i = 0; query[i] != '\0'; i++)
            {   
                //printf("%c\n", query[i]);
                if (query[i] == '+')
                {
                    query[i] = ' ';
                }
                
            }

            


            int udp_sock;
            struct sockaddr_in db_addr;
    
            // Create a UDP socket
            if ((udp_sock = socket(AF_INET, SOCK_DGRAM, 0)) < 0) {
                perror("socket");
                close(new_fd);
                continue;;
            }

            db_addr.sin_family = AF_INET;
            db_addr.sin_port = htons(dbport);
            inet_pton(AF_INET, DBADDR, &db_addr.sin_addr);

            // Send the search query to the database server
            sendto(udp_sock, query, strlen(query), 0, (struct sockaddr *) &db_addr, sizeof(db_addr));

            fd_set fds;
            struct timeval timeout;
            FD_ZERO(&fds);
            FD_SET(udp_sock, &fds);

            timeout.tv_sec = 5;  // 5-second timeout
            timeout.tv_usec = 0;


            //printf("here\n");
            //fflush(stdout);

            char buffer[4096];
            int m = 0;
            while (1) {
                //printf("in loop\n");
                //fflush(stdout);
                int sel = select(udp_sock + 1, &fds, NULL, NULL, &timeout);
                if (sel == 0) {
                    // Timeout occurred
                    send_response_header(new_fd, "408 Request Timeout", strlen("<html><body><h1>408 Request Timeout</h1></body></html>"));
                    n = write(new_fd, "<html><body><h1>408 Request Timeout</h1></body></html>", strlen("<html><body><h1>408 Request Timeout</h1></body></html>"));
                    printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "408 Request Timeout");
                    //printf("%d\n",n);
                    //printf("%ld\n", strlen("<html><body><h1>408 Request Timeout</h1></body></html>"));
                    //fflush(stdout);
                    timeout.tv_sec = 5;  // 5-second timeout
                    timeout.tv_usec = 0;

                    //close(udp_sock);
                    //close(new_fd);
                    break;
                } else if (sel < 0) {
                    perror("select");
                    break;
                }

                ssize_t bytes_received = recvfrom(udp_sock, buffer, sizeof(buffer), 0, NULL, NULL);
                if (bytes_received < 0) {
                    perror("recvfrom");
                    break;
                }
                buffer[bytes_received] = '\0';

                if (strcmp(buffer, "File Not Found") == 0) {
                    send_response_header(new_fd, "404 Not Found", strlen("<html><body><h1>404 Not Found</h1></body></html>"));
                    n = write(new_fd, "<html><body><h1>404 Not Found</h1></body></html>",strlen("<html><body><h1>404 Not Found</h1></body></html>"));
                    printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "404 Not Found");\
                    
                    break;
                } else if (strstr(buffer, "DONE") != NULL) {
                    n += write(new_fd, buffer, bytes_received - 4);
                    //close(udp_sock);
                    //close(new_fd);
                    break;
                } else {
                    // Relay the data to the client
                    if (m == 0) {
                        //send_response_header(new_fd, "200 OK",  file_stat.st_size);
                        printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr) , method, og, version, "200 OK");
                  //      printf("m = %d",m);
                    //    fflush(stdout);
                        char header[MAX_BUFFER_SIZE];
                        snprintf(header, sizeof(header),
                            "HTTP/1.0 %s\r\n"
                            "Content-Type: image/jpeg\r\n"
                            "\r\n",
                            "200 OK");
                       n =  write(new_fd, header, strlen(header));
                       //printf("%ld\n", strlen(header));
                        m++;
                    }
                //    printf("1\n");
              //      fflush(stdout);
                    n = write(new_fd, buffer, bytes_received);
                }
               // printf("%d\n", n);

            }
            //printf("final = %d\n", n);
            close(new_fd);
            close(udp_sock);
            continue;
            
            
            
        }





        else{

            //HTTP SERVER PART !


            char full_path[MAX_BUFFER_SIZE];
            snprintf(full_path, sizeof(full_path), "%s%s", "Webpage", uri);

            // Check if the path is a file or directory
            struct stat file_stat;
            if (stat(full_path, &file_stat) < 0) {
                send_response_header(new_fd, "404 Not Found",  strlen("<html><body><h1>404 Not Found</h1></body></html>"));
                n = write(new_fd, "<html><body><h1>404 Not Found</h1></body></html>", strlen("<html><body><h1>404 Not Found</h1></body></html>"));
                printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "404 Not Found");
                close(new_fd);
                continue;
            }

        
            if (S_ISDIR(file_stat.st_mode) && uri[strlen(uri) - 1] != '/') {
                strncat(full_path, "/index.html", sizeof(full_path) - strlen(full_path) - 1);
                if (stat(full_path, &file_stat) < 0 || S_ISDIR(file_stat.st_mode)) {
                    send_response_header(new_fd, "404 Not Found",  strlen("<html><body><h1>404 Not Found</h1></body></html>"));
                 n =    write(new_fd, "<html><body><h1>404 Not Found</h1></body></html>", strlen("<html><body><h1>404 Not Found</h1></body></html>"));
                    printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "404 Not Found");
                    close(new_fd);
                    continue;
                }
            }

            // Open the file for reading
            FILE *file_fd = fopen(full_path, "rb");
            if (file_fd == NULL) {
                perror("file error");
                //printf("womp womp");
                close(new_fd);
                continue;
            }

            // Send HTTP 200 OK header
        
            send_response_header(new_fd, "200 OK",  file_stat.st_size);
            printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, og, version, "200 OK");

            // Read the file in chunks and send to the client
            char file_buffer[4096];
            ssize_t bytes_read;
            while ((bytes_read = fread(file_buffer, 1, sizeof(file_buffer), file_fd)) > 0) {
                n = write(new_fd, file_buffer, bytes_read); 
            }

            fclose(file_fd);
    

            //printf("Send successfully completed...\n");
            // printf("%s \"%s %s %s\" %s\n", inet_ntoa((&their_addr)->sin_addr), method, uri, version, "501 Not Implemented");
		    close(new_fd);

        }
	}

    close(sockfd);


    return 0;
}
