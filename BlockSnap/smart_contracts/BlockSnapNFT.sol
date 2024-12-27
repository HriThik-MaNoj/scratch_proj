// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

contract BlockSnapNFT is ERC721URIStorage, Ownable {
    uint256 private _nextTokenId;
    uint256 private _nextSessionId;
    
    struct VideoChunk {
        uint256 sessionId;
        uint256 sequenceNumber;
        string videoCID;
        string metadataCID;
        uint256 timestamp;
    }
    
    // Mapping from token ID to IPFS CID
    mapping(uint256 => string) private _imageCIDs;
    
    // Video session mappings
    mapping(uint256 => address) private _sessionOwners;
    mapping(uint256 => VideoChunk[]) private _sessionChunks;
    mapping(uint256 => bool) private _activeSessions;
    
    // Events
    event PhotoMinted(uint256 indexed tokenId, address indexed owner, string ipfsCID, string metadataURI);
    event VideoSessionStarted(uint256 indexed sessionId, address indexed owner);
    event VideoChunkAdded(uint256 indexed sessionId, uint256 sequenceNumber, string videoCID);
    event VideoSessionEnded(uint256 indexed sessionId, uint256 totalChunks);
    
    constructor() ERC721("BlockSnap", "BSNAP") Ownable(msg.sender) {}
    
    /**
     * @dev Mint a new photo NFT
     * @param to The address that will own the minted token
     * @param imageCID The IPFS CID of the original photo
     * @param metadataURI The URI containing the metadata (usually IPFS URI)
     * @return uint256 The ID of the newly minted token
     */
    function mintPhoto(
        address to,
        string memory imageCID,
        string memory metadataURI
    ) public returns (uint256) {
        require(bytes(imageCID).length > 0, "Image CID cannot be empty");
        require(bytes(metadataURI).length > 0, "Metadata URI cannot be empty");
        
        uint256 tokenId = _nextTokenId++;
        
        _safeMint(to, tokenId);
        _setTokenURI(tokenId, metadataURI);
        _imageCIDs[tokenId] = imageCID;
        
        emit PhotoMinted(tokenId, to, imageCID, metadataURI);
        
        return tokenId;
    }
    
    /**
     * @dev Get the IPFS CID for a specific token
     * @param tokenId The ID of the token
     * @return string The IPFS CID of the original photo
     */
    function getImageCID(uint256 tokenId) public view returns (string memory) {
        require(tokenId < _nextTokenId && bytes(_imageCIDs[tokenId]).length > 0, "Token does not exist");
        return _imageCIDs[tokenId];
    }
    
    /**
     * @dev Verify if a photo exists and get its owner
     * @param imageCID The IPFS CID to verify
     * @return bool Whether the photo exists
     * @return address The owner of the photo (zero address if not found)
     */
    function verifyPhoto(string memory imageCID) public view returns (bool, address) {
        for (uint256 i = 0; i < _nextTokenId; i++) {
            if (keccak256(bytes(_imageCIDs[i])) == keccak256(bytes(imageCID))) {
                return (true, ownerOf(i));
            }
        }
        return (false, address(0));
    }
    
    /**
     * @dev Start a new video recording session
     * @return uint256 The ID of the new session
     */
    function startVideoSession() public returns (uint256) {
        uint256 sessionId = _nextSessionId++;
        _sessionOwners[sessionId] = msg.sender;
        _activeSessions[sessionId] = true;
        
        emit VideoSessionStarted(sessionId, msg.sender);
        return sessionId;
    }
    
    /**
     * @dev Add a video chunk to an active session
     * @param sessionId The ID of the session
     * @param sequenceNumber The sequence number of the chunk
     * @param videoCID The IPFS CID of the video chunk
     * @param metadataCID The IPFS CID of the chunk metadata
     */
    function addVideoChunk(
        uint256 sessionId,
        uint256 sequenceNumber,
        string memory videoCID,
        string memory metadataCID
    ) public {
        require(_activeSessions[sessionId], "Session is not active");
        require(_sessionOwners[sessionId] == msg.sender, "Not session owner");
        require(bytes(videoCID).length > 0, "Video CID cannot be empty");
        
        VideoChunk memory chunk = VideoChunk({
            sessionId: sessionId,
            sequenceNumber: sequenceNumber,
            videoCID: videoCID,
            metadataCID: metadataCID,
            timestamp: block.timestamp
        });
        
        _sessionChunks[sessionId].push(chunk);
        emit VideoChunkAdded(sessionId, sequenceNumber, videoCID);
    }
    
    /**
     * @dev End a video recording session
     * @param sessionId The ID of the session to end
     */
    function endVideoSession(uint256 sessionId) public {
        require(_activeSessions[sessionId], "Session is not active");
        require(_sessionOwners[sessionId] == msg.sender, "Not session owner");
        
        _activeSessions[sessionId] = false;
        emit VideoSessionEnded(sessionId, _sessionChunks[sessionId].length);
    }
    
    /**
     * @dev Get all chunks for a video session
     * @param sessionId The ID of the session
     * @return VideoChunk[] Array of video chunks
     */
    function getSessionChunks(uint256 sessionId) public view returns (VideoChunk[] memory) {
        return _sessionChunks[sessionId];
    }
    
    /**
     * @dev Check if a session is active
     * @param sessionId The ID of the session
     * @return bool Whether the session is active
     */
    function isSessionActive(uint256 sessionId) public view returns (bool) {
        return _activeSessions[sessionId];
    }
    
    function getNextTokenId() public view returns (uint256) {
        return _nextTokenId;
    }
    
    function burn(uint256 tokenId) public {
        require(ownerOf(tokenId) == msg.sender, "Not token owner");
        super._burn(tokenId);
    }
}