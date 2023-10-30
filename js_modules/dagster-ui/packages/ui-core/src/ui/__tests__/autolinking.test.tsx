import {render, screen, waitFor} from '@testing-library/react';
import React from 'react';

import {autolinkTextContent} from '../autolinking';

const Test = ({message, useIdleCallback}: {message: string; useIdleCallback: boolean}) => {
  const messageEl = React.createRef<HTMLDivElement>();
  React.useEffect(() => {
    if (messageEl.current) {
      // Note: window.requestIdleCallback is not available in the test runner,
      // requesting it tests the fallback async code path
      autolinkTextContent(messageEl.current, {useIdleCallback});
    }
  }, [message, messageEl, useIdleCallback]);

  return <div ref={messageEl}>{message}</div>;
};

describe('autolinking', () => {
  it('linkifies http, https, but not bare domains', async () => {
    const message = `
        This is my log message with some URLS.

        Linked:
        https://apple.com/
        http://dagsterlabs.com/
        http://127.0.0.1/my-internal-service?success=true
        http://username:password@127.0.0.1:8000/my-internal-service?success=true#paragraph-2

        Not linked:
        google.com
        idea.io
        tel://5402502334
        mailto:bengotow@dagsterlabs.com
        ftp://apple.com

        Edge cases:
        https://www.w3.org/TR/html-aria/#docconformance
        https://www.zoom.us/j/7647885554 // looks like a phone number

        Google maps worst case scenario:
        https://www.google.com/maps/place/Nashville,+TN/@36.1865271,-86.9503948,11z/data=!3m1!4b1!4m6!3m5!1s0x8864ec3213eb903d:0x7d3fb9d0a1e9daa0!8m2!3d36.1626638!4d-86.7816016!16zL20vMDVqYm4?entry=ttu
        `;

    const rendered = render(<Test message={message} useIdleCallback={false} />);

    waitFor(() => expect(screen.getByRole('link')).toBeDefined());

    const links = screen.getAllByRole('link');
    const hrefs = Array.from(links).map((el) => el.getAttribute('href'));
    expect(hrefs).toEqual([
      'https://apple.com/',
      'http://dagsterlabs.com/',
      'http://127.0.0.1/my-internal-service?success=true',
      'http://username:password@127.0.0.1:8000/my-internal-service?success=true#paragraph-2',
      'https://www.w3.org/TR/html-aria/#docconformance',
      'https://www.zoom.us/j/7647885554',
      'https://www.google.com/maps/place/Nashville,+TN/@36.1865271,-86.9503948,11z/data=!3m1!4b1!4m6!3m5!1s0x8864ec3213eb903d:0x7d3fb9d0a1e9daa0!8m2!3d36.1626638!4d-86.7816016!16zL20vMDVqYm4?entry=ttu',
    ]);

    expect(rendered.container.textContent!.trim()).toEqual(message.trim());
  });

  it('linkifies URLs in the text without altering the node text content', async () => {
    const rendered = render(<Test message={LongMessage} useIdleCallback={false} />);

    waitFor(() => expect(screen.getByRole('link')).toBeDefined());

    const links = screen.getAllByRole('link');
    const hrefs = Array.from(links).map((el) => el.getAttribute('href'));
    expect(hrefs).toEqual([
      'https://cloud.google.com/dataproc/',
      'https://cloud.google.com/dataproc/',
      'https://www.ietf.org/rfc/rfc1035.txt',
      'https://www.ietf.org/rfc/rfc1035.txt',
      'https://dataproc.googleapis.com/',
    ]);

    expect(rendered.container.textContent!.trim()).toEqual(LongMessage.trim());
  });

  it('linkifies URLs in the text in async chunks if useIdleCallback is requested but not available', async () => {
    expect('useIdleCallback' in window).toEqual(false);

    const rendered = render(<Test message={LongMessage} useIdleCallback={true} />);

    await waitFor(() => {
      const links = screen.getAllByRole('link');
      const hrefs = Array.from(links).map((el) => el.getAttribute('href'));
      expect(hrefs).toEqual([
        'https://cloud.google.com/dataproc/',
        'https://cloud.google.com/dataproc/',
        'https://www.ietf.org/rfc/rfc1035.txt',
        'https://www.ietf.org/rfc/rfc1035.txt',
        'https://dataproc.googleapis.com/',
      ]);
    });
    expect(rendered.container.textContent!.trim()).toEqual(LongMessage.trim());
  });
});

const LongMessage = `
This is my log message with some https://cloud.google.com/dataproc/ docs: {
    "kind": "discovery#restDescription",
    "description": "Manages Hadoop-based clusters and jobs on Google Cloud Platform.",
    "servicePath": "",
    "basePath": "",
    "revision": "20190627",
    "documentationLink": "https://cloud.google.com/dataproc/",
    "id": "dataproc:v1",
    "discoveryVersion": "v1",
    "schemas": {
        "Cluster": {
            "description": "Describes the identifying information, config, and status of a cluster of Compute Engine instances.",
            "type": "object",
            "properties": {
                "labels": {
                    "description": "Optional. The labels to associate with this cluster. Label keys must contain 1 to 63 characters, and must conform to RFC 1035 (https://www.ietf.org/rfc/rfc1035.txt). Label values may be empty, but, if present, must contain 1 to 63 characters, and must conform to RFC 1035 (https://www.ietf.org/rfc/rfc1035.txt). No more than 32 labels can be associated with a cluster.",
                    "type": "object",
                    "additionalProperties": {
                        "type": "string"
                    }
                },
                "status": {
                    "$ref": "ClusterStatus",
                    "description": "Output only. Cluster status."
                },
                "metrics": {
                    "$ref": "ClusterMetrics",
                    "description": "Contains cluster daemon metrics such as HDFS and YARN stats.Beta Feature: This report is available for testing purposes only. It may be changed before final release."
                },
                "config": {
                    "$ref": "ClusterConfig",
                    "description": "Required. The cluster config. Note that Cloud Dataproc may set default values, and values may change when clusters are updated."
                },
                "statusHistory": {
                    "type": "array",
                    "items": {
                        "$ref": "ClusterStatus"
                    },
                    "description": "Output only. The previous cluster status."
                },
                "clusterUuid": {
                    "description": "Output only. A cluster UUID (Unique Universal Identifier). Cloud Dataproc generates this value when it creates the cluster.",
                    "type": "string"
                },
                "clusterName": {
                    "type": "string",
                    "description": "Required. The cluster name. Cluster names within a project must be unique. Names of deleted clusters can be reused."
                },
                "projectId": {
                    "description": "Required. The Google Cloud Platform project ID that the cluster belongs to.",
                    "type": "string"
                }
            },
            "id": "Cluster"
        },
    },
    "version": "v1",
    "baseUrl": "https://dataproc.googleapis.com/"
}
`;
