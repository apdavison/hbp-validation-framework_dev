import React from 'react';
import Grid from '@material-ui/core/Grid';
import Box from '@material-ui/core/Box';
import IconButton from '@material-ui/core/IconButton';
import CloudDownloadIcon from '@material-ui/icons/CloudDownload';
import Markdown from './Markdown';
import { Typography } from '@material-ui/core';

function InstanceParameter(props) {
	if (props.value) {
		return <Typography variant="body2"><b>{props.label}: </b>{props.value}</Typography>
	} else {
		return ""
	}
}

export default function ModelDetailContent(props) {
	return (
		<React.Fragment>
			<Grid container xs={9} direction="column" item={true}>
				<Grid item>
					<Box p={2}>
						<Typography><b>Description: </b></Typography>
						<Markdown>{props.description}</Markdown>
					</Box>
				</Grid>
				<Grid item>
					<Box px={2} pb={0}>
						<Typography variant="subtitle1"><b>Versions</b></Typography>
					</Box>
					{props.instances.map(instance => (
						<Box m={2} p={2} pb={0} style={{ backgroundColor: '#eeeeee' }} key={instance.id}>
							<Typography variant="subtitle2">{instance.version}</Typography>
							<Typography variant="body2" color="textSecondary">{instance.timestamp}</Typography>
							<InstanceParameter label="Description" value={instance.description} />
							<InstanceParameter label="Source" value={instance.source} />
							<InstanceParameter label="Parameters" value={instance.parameters} />
							<InstanceParameter label="Morphology" value={instance.morphology} />
							<InstanceParameter label="Code format" value={instance.code_format} />
							<InstanceParameter label="License" value={instance.license} />
							<Typography variant="caption" color="textSecondary">ID: {instance.id}</Typography>
							<IconButton aria-label="download code" href={instance.source}>
								<CloudDownloadIcon />
							</IconButton>
						</Box>
					))}
				</Grid>

				<Grid item>
					{/* todo: images */}
				</Grid>
			</Grid>
		</React.Fragment>
	);
}


// {
//   "code_format" : "nest, dpsnn",
//   "description" : "",
//   "hash" : "",
//   "id" : "9f4d1284-c5c1-43e9-b922-03bbb29de830",
//   "license" : "All Rights Reserved",
//   "parameters" : "",
//   "source" : "https://collab.humanbrainproject.eu/#/collab/11175/nav/83589",
//   "timestamp" : "2018-10-05T12:32:57.352445+00:00",
//   "uri" : "https://nexus.humanbrainproject.org/v0/data/modelvalidation/simulation/modelinstance/v0.1.1/9f4d1284-c5c1-43e9-b922-03bbb29de830",
//   "version" : "00.01.00"
// }